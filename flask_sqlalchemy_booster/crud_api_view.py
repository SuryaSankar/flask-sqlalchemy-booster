from flask.views import MethodView
from .responses import (
    process_args_and_render_json_list, success_json, error_json,
    render_json_obj_with_requested_structure,
    render_json_list_with_requested_structure)
from flask import g, request
from flask_sqlalchemy_booster.responses import _serializable_params, serializable_obj, as_json
from schemalite import SchemaError
from schemalite.core import validate_object, validate_list_of_objects, json_encoder
from sqlalchemy.sql import sqltypes
import json


class CrudApiView(MethodView):

    _model_class_ = None
    _list_query_ = None
    _id_key_ = 'id'
    _schema_for_post_ = None
    _schema_for_put_ = None

    def get(self, _id):
        list_query = self._list_query_ or self._model_class_.query
        if _id is None:
            return process_args_and_render_json_list(list_query)
        else:
            if "," in _id:
                ids = [int(i) for i in _id.split(",")]
                resources = self._model_class_.get_all(ids)
                if all(r is None for r in resources):
                    return error_json(404, "No matching resources found")
                return render_json_list_with_requested_structure(
                    resources,
                    pre_render_callback=lambda output_dict: {
                        'status': 'partial_success' if None in resources else 'success',
                        'result': [
                            {'status': 'failure', 'error': 'Resource not found'}
                            if obj is None
                            else
                            {'status': 'success', 'result': obj}
                            for obj in output_dict['result']]})
                return process_args_and_render_json_list(
                    self._model_class_.query.filter(
                        self._model_class_.primary_key().in_(ids)))
            return render_json_obj_with_requested_structure(
                self._model_class_.get(_id, key=self._id_key_))

    def post(self):
        if self._schema_for_post_:
            try:
                if isinstance(g.json, list):
                    self._schema_for_post_.validate_list(g.json)
                else:
                    self._schema_for_post_.validate(g.json)
            except SchemaError as e:
                return error_json(400, e.value)
            json_data = g.json
            # json_data = self._schema_for_post_.adapt(g.json)
        else:
            json_data = g.json
        if isinstance(g.json, list):
            return render_json_list_with_requested_structure(
                self._model_class_.create_all(json_data))
        return render_json_obj_with_requested_structure(
            self._model_class_.create(**json_data))

    def put(self, _id):
        obj = self._model_class_.get(_id, key=self._id_key_)
        if self._schema_for_put_:
            try:
                self._schema_for_put_.validate(g.json)
            except SchemaError as e:
                return error_json(400, e.value)
            json_data = self._schema_for_put_.adapt(g.json)
        else:
            json_data = g.json
        return render_json_obj_with_requested_structure(obj.update(**json_data))

    def patch(self, _id):
        obj = self._model_class_.get(_id, key=self._id_key_)
        json_data = g.json
        return render_json_obj_with_requested_structure(obj.update(**json_data))

    def delete(self, _id):
        obj = self._model_class_.get(_id, key=self._id_key_)
        obj.delete()
        return success_json()


def register_crud_api_view(view, bp_or_app, endpoint, url_slug):
    bp_or_app.add_url_rule(
        '/%s/' % url_slug, defaults={'_id': None},
        view_func=view.as_view('%s__INDEX' % endpoint), methods=['GET', ])
    bp_or_app.add_url_rule(
        '/%s' % url_slug, view_func=view.as_view('%s__POST' % endpoint), methods=['POST', ])
    bp_or_app.add_url_rule(
        '/%s/<_id>' % url_slug, view_func=view.as_view('%s__GET' % endpoint),
        methods=['GET'])
    bp_or_app.add_url_rule(
        '/%s/<_id>' % url_slug, view_func=view.as_view('%s__PUT' % endpoint),
        methods=['PUT'])
    bp_or_app.add_url_rule(
        '/%s/<_id>' % url_slug, view_func=view.as_view('%s__PATCH' % endpoint),
        methods=['PATCH'])
    bp_or_app.add_url_rule(
        '/%s/<_id>' % url_slug, view_func=view.as_view('%s__DELETE' % endpoint),
        methods=['DELETE'])


def construct_get_view_function(model_class):
    def get(_id):
        if "," in _id:
            ids = [int(i) for i in _id.split(",")]
            resources = model_class.get_all(ids)
            if all(r is None for r in resources):
                return error_json(404, "No matching resources found")
            return render_json_list_with_requested_structure(
                resources,
                pre_render_callback=lambda output_dict: {
                    'status': 'partial_success' if None in resources else 'success',
                    'result': {
                        _id: {'status': 'failure', 'error': 'Resource not found'}
                        if obj is None
                        else {'status': 'success', 'result': obj}
                        for _id, obj in zip(ids, output_dict['result'])}
                }
            )
            return process_args_and_render_json_list(
                model_class.query.filter(
                    model_class.primary_key().in_(ids)))
        return render_json_obj_with_requested_structure(
            model_class.get(_id))
    return get


def construct_index_view_function(model_class, index_query=None):
    def index():
        return process_args_and_render_json_list(index_query or model_class)

    return index


def construct_post_view_function(model_class, input_schema=None):
    def post():
        schema = input_schema or model_class.input_data_schema()
        if isinstance(g.json, list):
            is_valid, errors = validate_list_of_objects(schema, g.json)
            input_objs = g.json
            if not is_valid:
                input_objs = [
                    input_obj if error is None else None
                    for input_obj, error in zip(g.json, errors)]
            resources = model_class.create_all(input_objs)
            return render_json_list_with_requested_structure(
                resources,
                pre_render_callback=lambda output_dict: {
                    'status': 'partial_success' if None in resources else 'success',
                    'result': [
                        {'status': 'failure', 'error': error}
                        if obj is None
                        else
                        {'status': 'success', 'result': obj}
                        for obj, error in zip(output_dict['result'], errors)]})
        else:
            is_valid, errors = validate_object(schema, g.json)
            if not is_valid:
                return error_json(400, errors)
            return render_json_obj_with_requested_structure(
                model_class.create(**g.json))
    return post


def construct_put_view_function(model_class, input_schema=None):
    def put(_id):
        schema = input_schema or model_class.input_data_schema()
        obj = model_class.get(_id)
        is_valid, errors = validate_object(
            schema, g.json, allow_required_fields_to_be_skipped=True,
            context={"existing_instance": obj})
        if not is_valid:
            return error_json(400, errors)
        return render_json_obj_with_requested_structure(obj.update(**g.json))

    return put


def construct_batch_put_view_function(model_class, input_schema=None):
    def batch_put():
        schema = input_schema or model_class.input_data_schema()
        output = {}
        obj_ids = g.json.keys()
        if type(model_class.primary_key().type)==sqltypes.Integer:
            obj_ids = [int(obj_id) for obj_id in obj_ids]
        existing_instances = dict(zip(obj_ids, model_class.get_all(obj_ids)))
        all_success = True
        any_success = False
        for obj_id, put_data_for_obj in g.json.items():
            output_key = obj_id
            if type(model_class.primary_key().type)==sqltypes.Integer:
                output_key = int(obj_id)
            existing_instance = existing_instances[output_key]
            if existing_instance is None:
                output[output_key] = {
                    "status": "failure",
                    "result": "Resource not found"
                }
                all_success = False
                any_success = any_success or False
            else:
                is_valid, errors = validate_object(
                    schema, put_data_for_obj, allow_required_fields_to_be_skipped=True,
                    context={"existing_instance": existing_instance})
                if is_valid:
                    updated_object = existing_instance.update_without_commit(
                        **put_data_for_obj)
                    output[output_key] = {
                        "status": "success",
                        "result": serializable_obj(
                            updated_object, **_serializable_params(request.args))
                    }
                    all_success = all_success and True
                    any_success = True
                else:
                    output[output_key] = {
                        "status": "failure",
                        "error": errors
                    }
                    all_success = False
                    any_success = any_success or False
        final_status = "success"
        if not all_success:
            if any_success:
                final_status = "partial_success"
            else:
                final_status = "failure"
        return as_json({
            "status": final_status,
            "result": output
        })
    return batch_put


def construct_patch_view_function(model_class, input_schema=None):
    def patch(_id):
        obj = model_class.get(_id)
        schema = input_schema or model_class.input_data_schema()
        is_valid, errors = validate_object(
            schema, g.json, allow_required_fields_to_be_skipped=True,
            context={"existing_instance": obj})
        if not is_valid:
            return error_json(400, errors)
        return render_json_obj_with_requested_structure(obj.update(**g.json))

    return patch


def construct_delete_view_function(model_class):
    def delete(_id):
        obj = model_class.get(_id)
        obj.delete()
        return success_json()
    return delete


def register_crud_routes_for_models(app_or_bp, registration_dict, register_schema_structure=True):
    models_and_urls = registration_dict.get('models_and_urls', [])
    if not hasattr(app_or_bp, "registered_models_and_crud_routes"):
        app_or_bp.registered_models_and_crud_routes = {
            "models_registered_for_views": [],
            "model_schemas": {

            },
            "views": {

            }
        }
    for _model, base_url in models_and_urls:
        view_dict_for_model = registration_dict.get('views', {}).get(_model, {})
        resource_name = _model.__tablename__

        if _model.__name__ not in app_or_bp.registered_models_and_crud_routes["models_registered_for_views"]:
            app_or_bp.registered_models_and_crud_routes["models_registered_for_views"].append(_model.__name__)
        model_schemas = app_or_bp.registered_models_and_crud_routes["model_schemas"]
        if _model.__name__ not in model_schemas:
            model_schemas[_model.__name__] = {
                "input_schema": _model.input_data_schema(),
                "output_schema": _model.output_data_schema(),
                "accepted_data_structure": _model.max_permissible_dict_structure()
            }
        for rel in _model.__mapper__.relationships.values():
            if rel.mapper.class_.__name__ not in model_schemas:
                model_schemas[rel.mapper.class_.__name__] = {
                    "input_schema": rel.mapper.class_.input_data_schema(),
                    "output_schema": rel.mapper.class_.output_data_schema(),
                    "accepted_data_structure": rel.mapper.class_.max_permissible_dict_structure()
                }

        index_dict = view_dict_for_model.get('index', {})
        index_func = index_dict.get('view_func', None) or construct_index_view_function(
            _model, index_query=index_dict.get('query'))
        index_url = index_dict.get('url', None) or "/%s" % base_url
        app_or_bp.route(
            index_url, methods=['GET'], endpoint='index_%s' % resource_name)(
            index_func)

        get_dict = view_dict_for_model.get('get', {})
        get_func = get_dict.get('view_func', None) or construct_get_view_function(_model)
        get_url = get_dict.get('url', None) or '/%s/<_id>' % base_url
        app_or_bp.route(
            get_url, methods=['GET'], endpoint='get_%s' % resource_name)(
            get_func)

        post_dict = view_dict_for_model.get('post', {})
        post_func = post_dict.get('view_func', None) or construct_post_view_function(
            _model, input_schema=post_dict.get('input_schema'))
        post_url = post_dict.get('url', None) or "/%s" % base_url
        app_or_bp.route(
            post_url, methods=['POST'], endpoint='post_%s' % resource_name)(
            post_func)

        put_dict = view_dict_for_model.get('put', {})
        put_func = put_dict.get('view_func', None) or construct_put_view_function(
            _model, input_schema=put_dict.get('input_schema'))
        put_url = put_dict.get('url', None) or "/%s/<_id>" % base_url
        app_or_bp.route(
            put_url, methods=['PUT'], endpoint='put_%s' % resource_name)(
            put_func)

        batch_put_dict = view_dict_for_model.get('batch_put', {})
        batch_put_func = batch_put_dict.get('view_func', None) or construct_batch_put_view_function(
            _model, input_schema=batch_put_dict.get('input_schema'))
        batch_put_url = batch_put_dict.get('url', None) or "/%s" % base_url
        app_or_bp.route(
            batch_put_url, methods=['PUT'], endpoint='batch_put_%s' % resource_name)(
            batch_put_func)

        patch_dict = view_dict_for_model.get('patch', {})
        patch_func = put_dict.get('view_func', None) or construct_patch_view_function(
            _model, input_schema=patch_dict.get('input_schema'))
        patch_url = patch_dict.get('url', None) or "/%s/<_id>" % base_url
        app_or_bp.route(
            patch_url, methods=['PATCH'], endpoint='patch_%s' % resource_name)(
            patch_func)

        delete_dict = view_dict_for_model.get('delete', {})
        delete_func = delete_dict.get('view_func', None) or construct_delete_view_function(
            _model)
        delete_url = delete_dict.get('url', None) or "/%s/<_id>" % base_url
        app_or_bp.route(
            delete_url, methods=['DELETE'], endpoint='delete_%s' % resource_name)(
            delete_func)

        views = app_or_bp.registered_models_and_crud_routes["views"]
        if _model.__name__ not in views:
            views[_model.__name__] = {
                'index': {
                    'url': index_url
                },
                'get': {
                    'url': get_url
                },
                'post': {
                    'url': post_url
                },
                'put': {
                    'url': put_url
                },
                'batch_put': {
                    'url': batch_put_url
                },
                'patch': {
                    'url': patch_url
                },
                'delete': {
                    'url': delete_url
                },
            }
        if 'input_schema' in post_dict:
            views[_model.__name__]['post']['input_schema'] = post_dict['input_schema']
        if 'input_schema' in put_dict:
            views[_model.__name__]['put']['input_schema'] = put_dict['input_schema']
        if 'input_schema' in batch_put_dict:
            views[_model.__name__]['batch_put']['input_schema'] = batch_put_dict['input_schema']