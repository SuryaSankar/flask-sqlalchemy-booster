from flask.json import _json
from flask_sqlalchemy import _BoundDeclarativeMeta
from flask import Response, request, render_template, g
from functools import wraps
from toolspy import deep_group, merge, add_kv_to_dict, boolify, all_subclasses
import inspect
from .json_encoder import json_encoder
from .query_booster import QueryBooster
from sqlalchemy.sql import sqltypes
from decimal import Decimal
import dateutil.parser
import math
from flask_sqlalchemy import Pagination
import traceback
from schemalite.core import validate_object
from schemalite.validators import is_a_type_of, is_a_list_of_types_of
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.query import Query
from sqlalchemy import or_, and_
from .utils import type_coerce_value


RESTRICTED = ['limit', 'sort', 'orderby', 'groupby', 'attrs',
              'rels', 'expand', 'offset', 'page', 'per_page']

PER_PAGE_ITEMS_COUNT = 20

OPERATORS = ['~', '=', '>', '<', '>=', '!', '<=']
OPERATOR_FUNC = {
    '~': 'ilike', '=': '__eq__', '>': '__gt__', '<': '__lt__',
    '>=': '__ge__', '<=': '__le__', '!': '__ne__', '!=': '__ne__',
    'in': 'in_'
}


def json_dump(obj):
    return _json.dumps(
        obj,
        default=json_encoder)


def json_response(json_string, status=200):
    return Response(json_string, status, mimetype='application/json')


def serializable_obj(
        obj, attrs_to_serialize=None, rels_to_expand=None,
        group_listrels_by=None, rels_to_serialize=None,
        key_modifications=None, dict_struct=None,
        dict_post_processors=None):
    if obj:
        if hasattr(obj, 'todict'):
            return obj.todict(
                attrs_to_serialize=attrs_to_serialize,
                rels_to_expand=rels_to_expand,
                group_listrels_by=group_listrels_by,
                rels_to_serialize=rels_to_serialize,
                key_modifications=key_modifications,
                dict_struct=dict_struct,
                dict_post_processors=dict_post_processors)
        return str(obj)
    return None


def serialized_obj(obj, attrs_to_serialize=None,
                   rels_to_expand=None,
                   group_listrels_by=None,
                   rels_to_serialize=None,
                   key_modifications=None,
                   dict_struct=None,
                   dict_post_processors=None):
    return serializable_obj(
        obj,
        attrs_to_serialize=attrs_to_serialize,
        rels_to_expand=rels_to_expand, 
        group_listrels_by=group_listrels_by,
        rels_to_serialize=rels_to_serialize,
        key_modifications=key_modifications,
        dict_struct=dict_struct,
        dict_post_processors=dict_post_processors)


def serializable_list(
        olist, attrs_to_serialize=None, rels_to_expand=None,
        group_listrels_by=None, rels_to_serialize=None,
        key_modifications=None, groupby=None, keyvals_to_merge=None,
        preserve_order=False, dict_struct=None, dict_post_processors=None):
    """
    Converts a list of model instances to a list of dictionaries
    using their `todict` method.

    Args:
        olist (list): The list of instances to convert
        attrs_to_serialize (list, optional): To be passed as an argument
            to the `todict` method
        rels_to_expand (list, optional): To be passed as an argument
            to the `todict` method
        group_listrels_by (dict, optional): To be passed as an argument
            to the `todict` method
        rels_to_serialize (list, optional): To be passed as an argument
            to the `todict` method
        key_modifications (dict, optional): To be passed as an argument
            to the `todict` method

        groupby (list, optional): An optional list of keys based on which
            the result list will be hierarchially grouped ( and converted
                into a dict)

        keyvals_to_merge (list of dicts, optional): A list of parameters
            to be merged with each dict of the output list
    """
    if groupby:
        if preserve_order:
            result = json_encoder(deep_group(
                olist, keys=groupby, serializer='todict',
                preserve_order=preserve_order,
                serializer_kwargs={
                    'rels_to_serialize': rels_to_serialize,
                    'rels_to_expand': rels_to_expand,
                    'attrs_to_serialize': attrs_to_serialize,
                    'group_listrels_by': group_listrels_by,
                    'key_modifications': key_modifications,
                    'dict_struct': dict_struct,
                    'dict_post_processors': dict_post_processors
                }))
        else:
            result = deep_group(
                olist, keys=groupby, serializer='todict',
                preserve_order=preserve_order,
                serializer_kwargs={
                    'rels_to_serialize': rels_to_serialize,
                    'rels_to_expand': rels_to_expand,
                    'attrs_to_serialize': attrs_to_serialize,
                    'group_listrels_by': group_listrels_by,
                    'key_modifications': key_modifications,
                    'dict_struct': dict_struct,
                    'dict_post_processors': dict_post_processors
                })
        return result
    else:
        result_list = map(
            lambda o: serialized_obj(
                o, attrs_to_serialize=attrs_to_serialize,
                rels_to_expand=rels_to_expand,
                group_listrels_by=group_listrels_by,
                rels_to_serialize=rels_to_serialize,
                key_modifications=key_modifications,
                dict_struct=dict_struct,
                dict_post_processors=dict_post_processors),
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


def structured(struct, wrap=True, meta=None, struct_key='result', pre_render_callback=None):
    output = struct
    if wrap:
        output = {'status': 'success', struct_key: struct}
        if meta:
            output = merge(output, meta)
    if pre_render_callback and callable(pre_render_callback):
        output = pre_render_callback(output)
    return output


def jsoned(struct, wrap=True, meta=None, struct_key='result', pre_render_callback=None):
    """ Provides a json dump of the struct

    Args:
        struct: The data to dump
        wrap (bool, optional): Specify whether to wrap the
            struct in an enclosing dict
        struct_key (str, optional): The string key which will
            contain the struct in the result dict
        meta (dict, optional): An optional dictonary to merge
            with the output dictionary.

    Examples:

        >>> jsoned([3,4,5])
        ... '{"status": "success", "result": [3, 4, 5]}'

        >>> jsoned([3,4,5], wrap=False)
        ... '[3, 4, 5]'

    """
    return _json.dumps(
        structured(
            struct, wrap=wrap, meta=meta, struct_key=struct_key,
            pre_render_callback=pre_render_callback),
        default=json_encoder)
    # if wrap:
        # output = {'status': 'success', struct_key: struct}
        # if meta:
        #     output = merge(output, meta)
        # return _json.dumps(output,
        #                    default=json_encoder)
    # else:
    #     return _json.dumps(struct,
    #                        default=json_encoder)


def jsoned_obj(obj, **kwargs):
    return jsoned(serializable_obj(obj, **kwargs))


def jsoned_list(olist, **kwargs):
    return jsoned(
        serializable_list(olist, **kwargs))


def as_json(struct, status=200, wrap=True, meta=None, pre_render_callback=None):
    return Response(
        jsoned(
            struct, wrap=wrap, meta=meta,
            pre_render_callback=pre_render_callback),
        status, mimetype='application/json')

def as_dict(o, attrs_to_serialize=None,
            rels_to_expand=None,
            rels_to_serialize=None,
            group_listrels_by=None,
            key_modifications=None,
            dict_struct=None,
            groupkeys=None,
            meta=None):
    return structured(serialized_obj(
        o, attrs_to_serialize=attrs_to_serialize,
        rels_to_expand=rels_to_expand,
        rels_to_serialize=rels_to_serialize,
        group_listrels_by=group_listrels_by,
        dict_struct=dict_struct,
        key_modifications=key_modifications),
        meta=meta)


def as_json_obj(o, attrs_to_serialize=None,
                rels_to_expand=None,
                rels_to_serialize=None,
                group_listrels_by=None,
                key_modifications=None,
                dict_struct=None,
                groupkeys=None,
                dict_post_processors=None,
                meta=None):
    s_obj = serialized_obj(
        o, attrs_to_serialize=attrs_to_serialize,
        rels_to_expand=rels_to_expand,
        rels_to_serialize=rels_to_serialize,
        group_listrels_by=group_listrels_by,
        dict_struct=dict_struct,
        key_modifications=key_modifications,
        dict_post_processors=dict_post_processors)
    return as_json(s_obj, meta=meta)


def as_dict_list(olist, attrs_to_serialize=None,
                 rels_to_expand=None,
                 rels_to_serialize=None,
                 group_listrels_by=None,
                 key_modifications=None,
                 dict_struct=None,
                 groupby=None,
                 preserve_order=False,
                 keyvals_to_merge=None,
                 meta=None):
    return structured(serializable_list(
        olist, attrs_to_serialize=attrs_to_serialize,
        rels_to_expand=rels_to_expand, rels_to_serialize=rels_to_serialize,
        group_listrels_by=group_listrels_by,
        key_modifications=key_modifications,
        dict_struct=dict_struct,
        groupby=groupby, keyvals_to_merge=keyvals_to_merge,
        preserve_order=preserve_order), meta=meta)


def as_json_list(olist, attrs_to_serialize=None,
                 rels_to_expand=None,
                 rels_to_serialize=None,
                 group_listrels_by=None,
                 key_modifications=None,
                 dict_struct=None,
                 groupby=None,
                 preserve_order=False,
                 keyvals_to_merge=None,
                 dict_post_processors=None,
                 meta=None, pre_render_callback=None):
    return as_json(serializable_list(
        olist, attrs_to_serialize=attrs_to_serialize,
        rels_to_expand=rels_to_expand, rels_to_serialize=rels_to_serialize,
        group_listrels_by=group_listrels_by,
        key_modifications=key_modifications,
        groupby=groupby, keyvals_to_merge=keyvals_to_merge,
        dict_struct=dict_struct,
        preserve_order=preserve_order,
        dict_post_processors=dict_post_processors), meta=meta, pre_render_callback=pre_render_callback)


def appropriate_json(olist, **kwargs):
    if len(olist) == 1:
        return as_json_obj(olist[0], **kwargs)
    return as_json_list(olist, **kwargs)


def success_json():
    return Response(jsoned({'status': 'success'}, wrap=False),
                    200, mimetype='application/json')


def error_json(status_code, error=None):
    return Response(_json.dumps({
        'status': 'failure',
        'error': error},
        default=json_encoder),
        status_code, mimetype='application/json')

ds_schema = {
    "fields": {
        "attrs": {
            "required": False,
            "validators": [is_a_list_of_types_of(str, unicode)]
        },
        "rels": {
            "required": False,
            "validators": [is_a_type_of(dict)]
        }
    }
}


def _serializable_params(args, check_groupby=False):
    params = {}
    if '_ds' in args:
        params['dict_struct'] = _json.loads(args['_ds'])
        if isinstance(params['dict_struct'], str) or isinstance(params['dict_struct'], unicode):
            params['dict_struct'] = _json.loads(params['dict_struct'])
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
            params['rels_to_serialize'] = [
                (rel.partition(':')[0], rel.partition(':')[2]) for rel in rels.split(',')
                if ':' in rel]
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
        if 'preserve_order' in request.args:
            params['preserve_order'] = boolify(request.args.get('preserve_order'))
    return params


def params_for_serialization(
        attrs_to_serialize=None, rels_to_expand=None,
        rels_to_serialize=None, group_listrels_by=None,
        dict_struct=None,
        preserve_order=None, groupby=None, check_groupby=False):
    params = _serializable_params(request.args, check_groupby=check_groupby)
    if attrs_to_serialize is not None and 'attrs_to_serialize' not in params:
        params['attrs_to_serialize'] = attrs_to_serialize
    if rels_to_expand is not None and 'rels_to_expand' not in params:
        params['rels_to_expand'] = rels_to_expand
    if rels_to_serialize is not None and 'rels_to_serialize' not in params:
        params['rels_to_serialize'] = rels_to_serialize
    if group_listrels_by is not None and 'group_listrels_by' not in params:
        params['group_listrels_by'] = group_listrels_by
    if preserve_order is not None and 'preserve_order' not in params:
        params['preserve_order'] = preserve_order
    if groupby is not None and 'groupby' not in params:
        params['groupby'] = groupby
    if dict_struct is not None:
        if 'dict_struct' not in params:
            params['dict_struct'] = dict_struct
        else:
            params['dict_struct'] = merge(dict_struct, params['dict_struct'])
    return params


def as_list(func):
    """ A decorator used to return a JSON response of a list of model
        objects. It expects the decorated function to return a list
        of model instances. It then converts the instances to dicts
        and serializes them into a json response

        Examples:

            >>> @app.route('/api')
            ... @as_list
            ... def list_customers():
            ...     return Customer.all()

    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        if isinstance(response, Response):
            return response
        return as_json_list(
            response,
            **_serializable_params(request.args, check_groupby=True))
    return wrapper


# def type_coerce_value(column_type, value):
#     if value is None:
#         return None
#     if isinstance(value, unicode) or isinstance(value, str):
#         if value.lower() == 'none' or value.lower() == 'null' or value.strip() == '':
#             return None
#     if column_type is sqltypes.Integer:
#         value = int(value)
#     elif column_type is sqltypes.Numeric:
#         value = Decimal(value)
#     elif column_type is sqltypes.Boolean:
#         value = boolify(value)
#     elif column_type is sqltypes.DateTime:
#         value = dateutil.parser.parse(value)
#     elif column_type is sqltypes.Date:
#         value = dateutil.parser.parse(value).date()
#     return value


def modify_query_and_get_filter_function(query, keyword, value, op):
    if '.' in keyword:
        kw_split_arr = keyword.split('.')
        prefix_names = kw_split_arr[:-1]
        attr_name = kw_split_arr[-1]
        _query = query
        model_class = query.model_class
        if prefix_names[0] in query.model_class._decl_class_registry:
            for class_name in prefix_names:
                if class_name not in query.model_class._decl_class_registry:
                    return (query, None)
                model_class = query.model_class._decl_class_registry[
                    class_name]
                if model_class not in [entity.class_ for entity in _query._join_entities]:
                    _query = _query.join(model_class)

        elif prefix_names[0] in query.model_class.all_keys():
            model_class = query.model_class
            for rel_or_proxy_name in prefix_names:
                if rel_or_proxy_name in model_class.relationship_keys():
                    mapped_rel = next(
                        r for r in model_class.__mapper__.relationships
                        if r.key == rel_or_proxy_name)
                    model_class = mapped_rel.mapper.class_
                    if model_class not in [entity.class_ for entity in _query._join_entities]:
                        _query = _query.join(model_class)
                elif rel_or_proxy_name in model_class.association_proxy_keys():
                    assoc_proxy = getattr(model_class, rel_or_proxy_name)
                    assoc_rel = next(
                        r for r in model_class.__mapper__.relationships
                        if r.key == assoc_proxy.target_collection)
                    assoc_rel_class = assoc_rel.mapper.class_
                    _query = _query.join(assoc_rel_class)
                    actual_rel_in_assoc_class = next(
                        r for r in assoc_rel_class.__mapper__.relationships
                        if r.key == assoc_proxy.value_attr)
                    model_class = actual_rel_in_assoc_class.mapper.class_
                    if model_class not in [entity.class_ for entity in _query._join_entities]:
                        _query = _query.join(model_class)
    else:
        model_class = query.model_class
        attr_name = keyword
        _query = query
        counter = 0  # to prevent infinite loop by some mistake

        while attr_name in model_class.association_proxy_keys() and counter < 10:
            counter += 1
            assoc_proxy = getattr(model_class, attr_name)
            assoc_rel = next(
                r for r in model_class.__mapper__.relationships
                if r.key == assoc_proxy.target_collection)
            prev_model_class = model_class
            model_class = assoc_rel.mapper.class_
            attr_name = assoc_proxy.value_attr
            if model_class not in [entity.class_ for entity in _query._join_entities]:
                # _query = _query.join(model_class)
                # Commenting this out because it is not possibel to directly
                # join a class when there are multiple foreign keys to it.
                # Instead it is preferable to join by mentioning the relationshp
                # itself.
                _query = _query.join(getattr(prev_model_class, assoc_rel.key))

    columns = getattr(
        getattr(model_class, '__mapper__'),
        'columns')
    column_type = None
    if attr_name in columns:
        column_type = type(
            columns[attr_name].type)
    if op == '~':
        value = "%{0}%".format(value)
    if op in ['=', '>', '<', '>=', '<=', '!', '!=']:
        if attr_name in columns:
            if value is not None and not isinstance(value, bool):
                # if value.lower() == 'none' or value.lower() == 'null' or value.strip() == '':
                #     value = None
                # else:
                value = type_coerce_value(column_type, value)
    elif op == 'in':
        value = map(lambda v: type_coerce_value(column_type, v), value)

    if hasattr(model_class, attr_name):
        return (_query, getattr(
            getattr(model_class, attr_name), OPERATOR_FUNC[op])(value))
    else:
        subcls_filters = []
        for subcls in all_subclasses(model_class):
            if attr_name in subcls.column_keys():
                if '.' in keyword:
                    if not _query.is_joined_with(subcls):
                        _query = _query.join(subcls)
                subcls_filters.append(
                    getattr(
                        getattr(subcls, attr_name),
                        OPERATOR_FUNC[op]
                    )(value)
                )
        if len(subcls_filters) > 0:
            return (_query, or_(*subcls_filters))
            # return _query.filter(or_(*subcls_filters))
        return (query, None)


def filter_query_with_key(query, keyword, value, op):
    _query, filter_func = modify_query_and_get_filter_function(
        query, keyword, value, op)
    if filter_func is not None:
        return _query.filter(filter_func)
    return query


def convert_filters_to_sqlalchemy_filter(query, filters, connector):
    sqfilters = []
    for f in filters:
        if "c" in f:
            sub_sq_filter = convert_filters_to_sqlalchemy_filter(
                query, f['f'], f['c'])
            if sub_sq_filter is not None:
                sqfilters.append(sub_sq_filter)
        else:
            query, sqfilter = modify_query_and_get_filter_function(
                query, f["k"], f["v"], f["op"])
            sqfilters.append(sqfilter)
    if len(sqfilters) > 0:
        if connector == 'AND':
            return and_(*sqfilters)
        if connector == 'OR':
            return or_(*sqfilters)
    return None


def filter_query_using_filters_list(result, filters_dict):
    """
    filters = {
        "c": "AND",
        "f": [
            {
                "k": "layout_id",
                "op": "=",
                "v": 1
            },
            {
                "k": "created_at",
                "op": ">=",
                "v": "2014-11-10T11:53:33"
            },
            {
                "c": "OR",
                "f": [
                    {
                        "k": "accepted",
                        "op": "=",
                        "v": true
                    },
                    {
                        "k": "accepted",
                        "op": "=",
                        "v": null
                    }
                ]
            }
        ]
    }
    """
    if not (isinstance(result, Query) or isinstance(result, QueryBooster)):
        if isinstance(result, _BoundDeclarativeMeta) and class_mapper(
                result).polymorphic_on is not None:
            result = result.query.with_polymorphic('*')
        else:
            result = result.query
    filters = filters_dict['f']
    connector = filters_dict.get('c') or 'AND'
    sqfilter = convert_filters_to_sqlalchemy_filter(result, filters, connector)
    if sqfilter is not None:
        result = result.filter(sqfilter)
    return result
    # for f in filters:
    #     if "c" in f:
    #         if f['c'] == 'AND':
    #             subfilters = f['f']
    #     else:
    #         result = filter_query_with_key(
    #             result, f["k"], f["v"], f["op"])
    # return result


def filter_query_using_args(result, args_to_skip=[]):
    if not (isinstance(result, Query) or isinstance(result, QueryBooster)):
        if isinstance(result, _BoundDeclarativeMeta) and class_mapper(
                result).polymorphic_on is not None:
            result = result.query.with_polymorphic('*')
        else:
            result = result.query
    for kw in request.args:
        if kw not in args_to_skip:
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
                    if value.lower() == 'none' or value.lower() == 'null' or value.strip() == '':
                        value = None
                    result = filter_query_with_key(result, kw, value, '=')
    return result


def fetch_results_in_requested_format(
        result, default_limit=None, default_sort=None, default_orderby=None,
        default_offset=None, default_page=None, default_per_page=None):
    limit = request.args.get('limit', default_limit)
    sort = request.args.get('sort', default_sort)
    orderby = request.args.get('orderby') or default_orderby or 'id'
    offset = request.args.get('offset', None) or default_offset
    page = request.args.get('page', None) or default_page
    per_page = request.args.get('per_page') or default_per_page or PER_PAGE_ITEMS_COUNT
    if sort:
        if sort == 'asc':
            result = result.asc(orderby)
        elif sort == 'desc':
            result = result.desc(orderby)
    if page:
        try:
            pagination = result.paginate(int(page), int(per_page))
        except:
            raise Exception("PAGE_NOT_FOUND")
        return pagination
    else:
        if limit:
            result = result.limit(limit)
        if offset:
            result = result.offset(int(offset) - 1)
        result = result.all()
    return result


def convert_result_to_response_structure(
        result, meta={}, attrs_to_serialize=None, rels_to_expand=None,
        rels_to_serialize=None, group_listrels_by=None,
        dict_struct=None,
        preserve_order=None, groupby=None):
    params_to_be_serialized = params_for_serialization(
        attrs_to_serialize=attrs_to_serialize, rels_to_expand=rels_to_expand,
        rels_to_serialize=rels_to_serialize,
        group_listrels_by=group_listrels_by,
        dict_struct=dict_struct,
        preserve_order=preserve_order, groupby=groupby,
        check_groupby=True)
    if isinstance(result, Pagination):
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', PER_PAGE_ITEMS_COUNT ))
        if result.total != 0 and int(page) > result.pages:
            return {
                "status": "failure",
                "error": "PAGE_NOT_FOUND",
                "total_pages": result.pages
            }
        pages_meta = {
            'total_pages': result.pages,
            'total_items': result.total,
            'page': page,
            'per_page': per_page,
            'curr_page_first_item_index': (page - 1) * per_page + 1,
            'curr_page_last_item_index': min(page * per_page, result.total)
        }
        if isinstance(meta, dict) and len(meta.keys()) > 0:
            pages_meta = merge(pages_meta, meta)
        return structured(
            serializable_list(result.items, **params_to_be_serialized),
            meta=pages_meta)
    if isinstance(meta, dict) and len(meta.keys()) > 0:
        kwargs = merge(params_to_be_serialized, {'meta': meta})
    else:
        kwargs = params_to_be_serialized
    return as_dict_list(result, **kwargs)


def decide_status_code_for_response(obj):
    status = 200
    if obj['status'] == 'failure':
        if obj['error'] == 'PAGE_NOT_FOUND':
            status = 404
        else:
            status = 400
    return status


def convert_result_to_response(result, **kwargs):
    obj = convert_result_to_response_structure(result, **kwargs)
    return json_response(json_dump(obj), status=decide_status_code_for_response(obj))


def convert_query_to_response_object(
        query, args_to_skip=[], meta={}, attrs_to_serialize=None, rels_to_expand=None,
        rels_to_serialize=None, group_listrels_by=None, dict_struct=None,
        preserve_order=None, groupby=None):
    return convert_result_to_response_structure(
        fetch_results_in_requested_format(
            filter_query_using_args(query, args_to_skip=args_to_skip)), 
        meta=meta, attrs_to_serialize=attrs_to_serialize, rels_to_expand=rels_to_expand,
        rels_to_serialize=rels_to_serialize, group_listrels_by=group_listrels_by,
        dict_struct=dict_struct,
        preserve_order=preserve_order, groupby=groupby)


def json_response_from_obj(obj):
    return json_response(json_dump(obj), decide_status_code_for_response(obj))


def template_response_from_obj(
        obj, template, keys_to_be_replaced={}, merge_keyvals={}):
    for k in keys_to_be_replaced:
        if k in obj:
            obj[keys_to_be_replaced[k]] = obj.pop(k)
    return render_template(template, **merge(obj, merge_keyvals))


def process_args_and_fetch_rows(
        q, default_limit=None, default_sort=None, default_orderby=None,
        default_offset=None, default_page=None, default_per_page=None):

    if isinstance(q, Response):
        return q

    if '_f' in request.args:
        filters = _json.loads(request.args['_f'])
        if isinstance(filters, str) or isinstance(filters, unicode):
            filters = _json.loads(filters)
        q = filter_query_using_filters_list(q, filters)

    filtered_query = filter_query_using_args(q)

    count_only = boolify(request.args.get('count_only', 'false'))
    if count_only:
        return as_json(filtered_query.count())

    result = fetch_results_in_requested_format(
        filtered_query,
        default_limit=default_limit,
        default_sort=default_sort,
        default_orderby=default_orderby,
        default_offset=default_offset,
        default_page=default_page,
        default_per_page=default_per_page
    )
    return result


def process_args_and_render_json_list(q, **kwargs):

    if isinstance(q, Response):
        return q

    if '_f' in request.args:
        filters = _json.loads(request.args['_f'])
        if isinstance(filters, str) or isinstance(filters, unicode):
            filters = _json.loads(filters)
        q = filter_query_using_filters_list(q, filters)

    filtered_query = filter_query_using_args(q)

    count_only = boolify(request.args.get('count_only', 'false'))
    if count_only:
        return as_json(filtered_query.count())

    try:
        result = fetch_results_in_requested_format(
            filtered_query,
            default_limit=kwargs.pop('default_limit', None),
            default_sort=kwargs.pop('default_sort', None),
            default_orderby=kwargs.pop('default_orderby', None),
            default_offset=kwargs.pop('default_offset', None),
            default_page=kwargs.pop('default_page', None),
            default_per_page=kwargs.pop('default_per_page', None))
    except:
        traceback.print_exc()
        per_page = request.args.get('per_page', PER_PAGE_ITEMS_COUNT)
        return as_json({
            "status": "failure",
            "error": "PAGE_NOT_FOUND",
            "total_pages": int(math.ceil(float(filtered_query.count()) / int(per_page)))
        }, status=404, wrap=False)

    return convert_result_to_response(result, **kwargs)


def merge_params_with_request_args_while_deep_merging_dict_struct(kwargs):
    params_from_request_args = _serializable_params(request.args)
    merged_params = merge(kwargs, params_from_request_args)
    if kwargs.get('dict_struct') and params_from_request_args.get('dict_struct'):
        merged_params['dict_struct'] = merge(
            kwargs['dict_struct'], params_from_request_args.get('dict_struct'))
    return merged_params


def render_json_obj_with_requested_structure(obj, **kwargs):
    if isinstance(obj, Response):
        return obj
    merged_params = merge_params_with_request_args_while_deep_merging_dict_struct(kwargs)
    return as_json_obj(obj, **merged_params)

def render_dict_with_requested_structure(obj, **kwargs):
    if isinstance(obj, Response):
        return obj
    merged_params = merge_params_with_request_args_while_deep_merging_dict_struct(kwargs)
    return as_dict(obj, **merged_params)


def serializable_obj_with_requested_structure(obj):
    if isinstance(obj, Response):
        return obj
    return serializable_obj(
        obj,
        **_serializable_params(request.args))


def render_json_list_with_requested_structure(obj, **kwargs):
    if isinstance(obj, Response):
        return obj
    merged_params = merge_params_with_request_args_while_deep_merging_dict_struct(kwargs)
    return as_json_list(obj, **merged_params)


def render_dict_list_with_requested_structure(obj, **kwargs):
    if isinstance(obj, Response):
        return obj

    return as_dict_list(
        obj, **merge_params_with_request_args_while_deep_merging_dict_struct(kwargs))


def as_processed_list(func):
    """ A decorator used to return a JSON response of a list of model
        objects. It differs from `as_list` in that it accepts a variety
        of querying parameters and can use them to filter and modify the
        results. It expects the decorated function to return either Model Class
        to query or a SQLAlchemy filter which exposes a subset of the instances
        of the Model class. It then converts the instances to dicts
        and serializes them into a json response

        Examples:

            >>> @app.route('/api/customers')
            ... @as_processed_list
            ... def list_all_customers():
            ...     return Customer

            >>> @app.route('/api/editors')
            ... @as_processed_list
            ... def list_editors():
            ...     return User.filter(role='editor')
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_argspec = inspect.getargspec(func)
        func_args = func_argspec.args
        for kw in request.args:
            if (kw in func_args and kw not in RESTRICTED and
                    not any(request.args.get(kw).startswith(op)
                            for op in OPERATORS)
                    and not any(kw.endswith(op) for op in OPERATORS)):
                kwargs[kw] = request.args.get(kw)
        func_output = func(*args, **kwargs)

        return process_args_and_render_json_list(func_output)

    return wrapper


def as_obj(func):
    """ A decorator used to return a JSON response with a dict
        representation of the model instance.  It expects the decorated function
        to return a Model instance. It then converts the instance to dicts
        and serializes it into a json response

        Examples:

            >>> @app.route('/api/shipments/<id>')
            ... @as_obj
            ... def get_shipment(id):
            ...     return Shipment.get(id)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        return render_json_obj_with_requested_structure(response)
    return wrapper


def as_list_or_obj(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return appropriate_json(
            func(*args, **kwargs),
            **_serializable_params(request.args))
    return wrapper
