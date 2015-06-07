from flask.json import _json
from flask import abort, Response, request
from functools import wraps
from toolspy import deep_group, merge, add_kv_to_dict, boolify
import inspect
from .json_encoder import json_encoder
from .query_booster import QueryBooster
from sqlalchemy.sql import sqltypes


RESTRICTED = ['limit', 'sort', 'orderby', 'groupby', 'attrs',
              'rels', 'expand', 'offset', 'page', 'per_page']

OPERATORS = ['~', '=', '>', '<', '>=', '!', '<=']
OPERATOR_FUNC = {
    '~': 'ilike', '=': '__eq__', '>': '__gt__', '<': '__lt__',
    '>': '__gt__', '>=': '__ge__', '<=': '__le__', '!': '__ne__'
}


def serializable_obj(
        obj, attrs_to_serialize=None, rels_to_expand=None,
        group_listrels_by=None, rels_to_serialize=None,
        key_modifications=None):
    if obj:
        if hasattr(obj, 'todict'):
            return obj.todict(
                attrs_to_serialize=attrs_to_serialize,
                rels_to_expand=rels_to_expand,
                group_listrels_by=group_listrels_by,
                rels_to_serialize=rels_to_serialize,
                key_modifications=key_modifications)
        return str(obj)
    return None


def serialized_obj(obj, attrs_to_serialize=None,
                   rels_to_expand=None,
                   group_listrels_by=None,
                   rels_to_serialize=None,
                   key_modifications=None):
    """
    Misnamed. Should be deprecated eventually.
    """
    return serializable_obj(
        obj, attrs_to_serialize, rels_to_expand, group_listrels_by,
        rels_to_serialize, key_modifications)


def serializable_list(
        olist, attrs_to_serialize=None, rels_to_expand=None,
        group_listrels_by=None, rels_to_serialize=None,
        key_modifications=None, groupby=None, keyvals_to_merge=None):
    if groupby:
        return deep_group(
            olist, keys=groupby, serializer='todict',
            serializer_kwargs={
                'rels_to_serialize': rels_to_serialize,
                'rels_to_expand': rels_to_expand,
                'attrs_to_serialize': attrs_to_serialize,
                'group_listrels_by': group_listrels_by,
                'key_modifications': key_modifications
            })
    else:
        result_list = map(
            lambda o: serialized_obj(
                o, attrs_to_serialize=attrs_to_serialize,
                rels_to_expand=rels_to_expand,
                group_listrels_by=group_listrels_by,
                rels_to_serialize=rels_to_serialize,
                key_modifications=key_modifications),
            olist)
        if keyvals_to_merge:
            result_list = [merge(obj_dict, kvdict)
                           for obj_dict, kvdict in
                           zip(result_list, keyvals_to_merge)]
        return result_list


def serialized_list(olist, **kwargs):
    """
    Misnamed. Should be deprecated eventually.
    """
    return map(
        lambda o: serialized_obj(o, **kwargs),
        olist)


def jsoned(struct, wrap=True, meta=None, wrap_key='result'):
    if wrap:
        output = {'status': 'success', wrap_key: struct}
        if meta:
            output = merge(output, meta)
        return _json.dumps(output,
                           default=json_encoder)
    else:
        return _json.dumps(struct,
                           default=json_encoder)


def jsoned_obj(obj, **kwargs):
    return jsoned(serialized_obj(obj, **kwargs))


def jsoned_list(olist, **kwargs):
    return jsoned(
        serialized_list(olist, **kwargs))


# def success_json():
#     return Response(jsoned({'status': 'success'}, wrap=False),
#                     200, mimetype='application/json')


def as_json(struct, status=200, wrap=True, meta=None):
    return Response(jsoned(struct, wrap=wrap, meta=meta),
                    status, mimetype='application/json')


def as_json_obj(o, attrs_to_serialize=None,
                rels_to_expand=None,
                rels_to_serialize=None,
                group_listrels_by=None,
                key_modifications=None,
                groupkeys=None,
                meta=None):
    return as_json(serialized_obj(
        o, attrs_to_serialize=attrs_to_serialize,
        rels_to_expand=rels_to_expand,
        rels_to_serialize=rels_to_serialize,
        group_listrels_by=group_listrels_by,
        key_modifications=key_modifications),
        meta=meta)


def as_json_list(olist, attrs_to_serialize=None,
                 rels_to_expand=None,
                 rels_to_serialize=None,
                 group_listrels_by=None,
                 key_modifications=None,
                 groupby=None,
                 keyvals_to_merge=None,
                 meta=None):
    return as_json(serializable_list(
        olist, attrs_to_serialize=attrs_to_serialize,
        rels_to_expand=rels_to_expand, rels_to_serialize=rels_to_serialize,
        group_listrels_by=group_listrels_by,
        key_modifications=key_modifications,
        groupby=groupby, keyvals_to_merge=keyvals_to_merge
        ), meta=meta)


def appropriate_json(olist, **kwargs):
    if len(olist) == 1:
        return as_json_obj(olist[0], **kwargs)
    return as_json_list(olist, **kwargs)


def _serializable_params(args, check_groupby=False):
    params = {}
    if 'attrs' in args:
        attrs = args.get('attrs')
        if attrs.lower() == 'none':
            params['attrs_to_serialize'] = []
        else:
            params['attrs_to_serialize'] = attrs.split(',')
    if 'rels' in args:
        rels = args.get('rels')
        if rels.lower() == 'none':
            params['rels_to_serialize'] = []
        else:
            params['rels_to_serialize'] = rels.split(',')
    if 'expand' in args:
        expand = args.get('expand')
        if expand.lower() == 'none':
            params['rels_to_expand'] = []
        else:
            params['rels_to_expand'] = expand.split(',')
    if 'grouprelby' in request.args:
        params['group_listrels_by'] = {
            arg.partition(':')[0]: arg.partition(':')[2].split(',')
            for arg in request.args.getlist('grouprelby')}
    if check_groupby and 'groupby' in request.args:
        params['groupby'] = request.args.get('groupby').split(',')
    return params


def as_list(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return as_json_list(
            func(*args, **kwargs),
            **_serializable_params(request.args, check_groupby=True))
    return wrapper


def filter_query_with_key(query, keyword, value, op):
    if '.' in keyword:

        # class_name = keyword.partition('.')[0]
        # attr_name = keyword.partition('.')[2]
        # if class_name not in query.model_class._decl_class_registry:
        #     return query
        # model_class = query.model_class._decl_class_registry[class_name]
        # # model_class = getattr(models, class_name)
        # _query = query.join(model_class)

        kw_split_arr = keyword.split('.')
        class_names = kw_split_arr[:-1]
        attr_name = kw_split_arr[-1]
        _query = query
        for class_name in class_names:
            if class_name not in query.model_class._decl_class_registry:
                return query
            model_class = query.model_class._decl_class_registry[class_name]
            # model_class = getattr(models, class_name)
            _query = _query.join(model_class)
    else:
        model_class = query.model_class
        attr_name = keyword
        _query = query
    if hasattr(model_class, attr_name):
        key = getattr(model_class, attr_name)
        if op == '~':
            value = "%{0}%".format(value)
        if op in ['=', '>', '<', '>=', '<=', '!']:
            columns = getattr(
                getattr(model_class, '__mapper__'),
                'columns')
            if attr_name in columns:
                column_type = type(
                    columns[attr_name].type)
                if column_type is sqltypes.Integer:
                    value = int(value)
                elif column_type is sqltypes.Boolean:
                    value = boolify(value)
        return _query.filter(getattr(
            key, OPERATOR_FUNC[op])(value))
    else:
        return query


def as_processed_list(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        limit = request.args.get('limit', None)
        sort = request.args.get('sort', None)
        orderby = request.args.get('orderby', 'id')
        offset = request.args.get('offset', None)
        page = request.args.get('page', None)
        per_page = request.args.get('per_page', 20)
        func_argspec = inspect.getargspec(func)
        func_args = func_argspec.args
        for kw in request.args:
            if (kw in func_args and kw not in RESTRICTED and
                    not any(request.args.get(kw).startswith(op)
                            for op in OPERATORS)
                    and not any(kw.endswith(op) for op in OPERATORS)):
                kwargs[kw] = request.args.get(kw)
        result = func(*args, **kwargs)
        if not isinstance(result, QueryBooster):
            result = result.query
        for kw in request.args:
            for op in OPERATORS:
                if kw.endswith(op):
                    result = filter_query_with_key(
                        result, kw.rstrip(op), request.args.get(kw), op)
                    break
                elif request.args.get(kw).startswith(op):
                    result = filter_query_with_key(
                        result, kw, request.args.get(kw).lstrip(op), op)
                    break
            else:
                # Well who would've thought that a for else will be appropriate
                # anywhere? Turns out it is here.
                if kw not in RESTRICTED:
                    value = request.args.get(kw)
                    if value.lower() == 'none':
                        value = None
                    result = filter_query_with_key(result, kw, value, '=')
        if sort:
            if sort == 'asc':
                result = result.asc(orderby)
            elif sort == 'desc':
                result = result.desc(orderby)
        if page:
            pagination = result.paginate(int(page), int(per_page))
            if pagination.total == 0:
                return as_json_list(
                    result,
                    **_serializable_params(request.args, check_groupby=True))
            if int(page) > pagination.pages:
                abort(404)
            return as_json_list(
                pagination.items,
                **add_kv_to_dict(
                    _serializable_params(request.args, check_groupby=True),
                    'meta', {'total_pages': pagination.pages,
                             'total_items': pagination.total
                             }))
        else:
            if limit:
                result = result.limit(limit)
            if offset:
                result = result.offset(int(offset)-1)
            result = result.all()
        return as_json_list(
            result,
            **_serializable_params(request.args, check_groupby=True)
            )
    return wrapper


def as_obj(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return as_json_obj(
            func(*args, **kwargs),
            **_serializable_params(request.args))
    return wrapper


def as_list_or_obj(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return appropriate_json(
            func(*args, **kwargs),
            **_serializable_params(request.args))
    return wrapper

