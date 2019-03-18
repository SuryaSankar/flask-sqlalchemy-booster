from flask.views import MethodView
from flask import g, request, Response,url_for
from schemalite import SchemaError
from schemalite.core import validate_object, validate_list_of_objects, json_encoder
from sqlalchemy.sql import sqltypes
import json
from toolspy import (
    all_subclasses, fetch_nested_key_from_dict, fetch_nested_key,
    delete_dict_keys, union, merge)
from copy import deepcopy
import inspect
from .responses import (
    as_dict,
    process_args_and_render_json_list, success_json, error_json,
    render_json_obj_with_requested_structure,
    render_json_list_with_requested_structure,
    render_dict_with_requested_structure,
    _serializable_params, serializable_obj, as_json,
    process_args_and_fetch_rows, convert_result_to_response)
import urllib
import functools
from ..utils import remove_empty_values_in_dict, save_file_from_request, convert_to_proper_types
import csv

def permit_only_allowed_fields(data, fields_allowed_to_be_set=None, fields_forbidden_from_being_set=None):
    if fields_allowed_to_be_set and len(fields_allowed_to_be_set) > 0:
        for k in data.keys():
            if k not in fields_allowed_to_be_set:
                del data[k]
    if fields_forbidden_from_being_set and len(fields_forbidden_from_being_set) > 0:
        delete_dict_keys(data, fields_forbidden_from_being_set)



def register_crud_routes_for_models(
        app_or_bp, registration_dict, register_schema_structure=True,
        allow_unknown_fields=False, cache_handler=None, exception_handler=None,
        tmp_folder_path="/tmp", forbidden_views=None, celery_worker=None):
    if not hasattr(app_or_bp, "registered_models_and_crud_routes"):
        app_or_bp.registered_models_and_crud_routes = {
            "models_registered_for_views": [],
            "model_schemas": {

            },
            "views": {

            }
        }
    app_or_bp.registration_dict = registration_dict
    model_schemas = app_or_bp.registered_models_and_crud_routes["model_schemas"]

    def populate_model_schema(modelcls, modelcls_key=None):
        if modelcls_key is None:
            modelcls_key = modelcls.__name__
        if modelcls._input_data_schema_:
            input_schema = deepcopy(modelcls._input_data_schema_)
        else:
            input_schema = modelcls.generate_input_data_schema()
        if modelcls in registration_dict and callable(registration_dict[modelcls].get('input_schema_modifier')):
            input_schema = registration_dict[modelcls]['input_schema_modifier'](input_schema)
        model_schemas[modelcls_key] = {
            "input_schema": input_schema,
            "output_schema": modelcls.output_data_schema(),
            "accepted_data_structure": modelcls.max_permissible_dict_structure()
        }
        for subcls in all_subclasses(modelcls):
            if subcls.__name__ not in model_schemas:
                model_schemas[subcls.__name__] = {
                    'is_a_polymorphically_derived_from': modelcls.__name__,
                    'polymorphic_identity': subcls.__mapper_args__['polymorphic_identity'] 
                }
        for rel in modelcls.__mapper__.relationships.values():
            if rel.mapper.class_.__name__ not in model_schemas:
                populate_model_schema(rel.mapper.class_)

    for _model_key, _model_dict in registration_dict.items():
        if isinstance(_model_key, str):
            _model = _model_dict['model_class']
            _model_name = _model_key
        else:
            _model = _model_key
            _model_name = _model.__name__
        base_url = _model_dict.get('url_slug')
        disabled_views = _model_dict.get('forbidden_views') or forbidden_views or []
        default_query_constructor = _model_dict.get('query_constructor')
        default_access_checker = _model_dict.get('access_checker')
        default_dict_post_processors = _model_dict.get('dict_post_processors')
        view_dict_for_model = _model_dict.get('views', {})
        dict_struct_for_model = _model_dict.get('dict_struct')
        fields_forbidden_from_being_set_for_all_views = _model_dict.get('fields_forbidden_from_being_set', [])
        enable_caching = _model_dict.get('enable_caching', False) and cache_handler is not None
        cache_timeout = _model_dict.get('cache_timeout')
        resource_name = _model_dict.get('resource_name') or _model.__tablename__

        if _model_name not in app_or_bp.registered_models_and_crud_routes["models_registered_for_views"]:
            app_or_bp.registered_models_and_crud_routes["models_registered_for_views"].append(_model_name)
        if _model_name not in model_schemas:
            populate_model_schema(_model, modelcls_key=_model_name)

        if _model._input_data_schema_:
            model_default_input_schema = deepcopy(_model._input_data_schema_)
        else:
            model_default_input_schema = _model.generate_input_data_schema()
        if callable(registration_dict[_model].get('input_schema_modifier')):
            model_default_input_schema = registration_dict[_model]['input_schema_modifier'](model_default_input_schema)

        views = app_or_bp.registered_models_and_crud_routes["views"]
        schemas_registry = {k: v.get('input_schema') for k, v in model_schemas.items()}
        if _model_name not in views:
            views[_model_name] = {}

        if 'index' not in disabled_views:
            index_dict = view_dict_for_model.get('index', {})
            if 'enable_caching' in index_dict:
                enable_caching = index_dict.get('enable_caching') and cache_handler is not None
            cache_key_determiner = index_dict.get('cache_key_determiner')
            cache_timeout = index_dict.get('cache_timeout') or cache_timeout
            index_func = index_dict.get('view_func', None) or construct_index_view_function(
                _model,
                index_query_creator=index_dict.get('query_constructor') or default_query_constructor,
                dict_struct=index_dict.get('dict_struct') or dict_struct_for_model,
                custom_response_creator=index_dict.get('custom_response_creator'),
                enable_caching=enable_caching,
                cache_handler=cache_handler, cache_key_determiner=cache_key_determiner,
                cache_timeout=cache_timeout, exception_handler=exception_handler,
                access_checker=index_dict.get('access_checker') or default_access_checker,
                default_limit=index_dict.get('default_limit'),
                default_sort=index_dict.get('default_sort'),
                default_orderby=index_dict.get('default_orderby'),
                default_offset=index_dict.get('default_offset'),
                default_page=index_dict.get('default_page'),
                default_per_page=index_dict.get('default_per_page'))
            index_url = index_dict.get('url', None) or "/%s" % base_url
            app_or_bp.route(
                index_url, methods=['GET'], endpoint='index_%s' % resource_name)(
                index_func)
            views[_model_name]['index'] = {'url': index_url}

        if 'get' not in disabled_views:
            get_dict = view_dict_for_model.get('get', {})
            if 'enable_caching' in get_dict:
                enable_caching = get_dict.get('enable_caching') and cache_handler is not None
            cache_key_determiner = get_dict.get('cache_key_determiner')
            cache_timeout = get_dict.get('cache_timeout') or cache_timeout
            get_func = get_dict.get('view_func', None) or construct_get_view_function(
                _model, registration_dict,
                permitted_object_getter=get_dict.get('permitted_object_getter') or _model_dict.get('permitted_object_getter'),
                get_query_creator=get_dict.get('query_constructor') or default_query_constructor,
                dict_struct=get_dict.get('dict_struct') or dict_struct_for_model,
                enable_caching=enable_caching,
                cache_handler=cache_handler, cache_key_determiner=cache_key_determiner,
                cache_timeout=cache_timeout, exception_handler=exception_handler,
                access_checker=get_dict.get('access_checker') or default_access_checker,
                dict_post_processors=get_dict.get('dict_post_processors') or default_dict_post_processors)
            get_url = get_dict.get('url', None) or '/%s/<_id>' % base_url
            app_or_bp.route(
                get_url, methods=['GET'], endpoint='get_%s' % resource_name)(
                get_func)
            views[_model_name]['get'] = {'url': get_url}

        if 'post' not in disabled_views:
            post_dict = view_dict_for_model.get('post', {})
            if callable(post_dict.get('input_schema_modifier')):
                post_input_schema = post_dict['input_schema_modifier'](deepcopy(model_default_input_schema))
            else:
                post_input_schema = model_default_input_schema
            post_func = post_dict.get('view_func', None) or construct_post_view_function(
                _model, post_input_schema,
                registration_dict=registration_dict,
                pre_processors=post_dict.get('pre_processors'),
                post_processors=post_dict.get('post_processors'),
                schemas_registry=schemas_registry,
                allow_unknown_fields=allow_unknown_fields,
                dict_struct=post_dict.get('dict_struct') or dict_struct_for_model,
                exception_handler=exception_handler,
                access_checker=post_dict.get('access_checker') or default_access_checker,
                fields_forbidden_from_being_set=union([
                    fields_forbidden_from_being_set_for_all_views,
                    post_dict.get('fields_forbidden_from_being_set', [])]))
            post_url = post_dict.get('url', None) or "/%s" % base_url
            app_or_bp.route(
                post_url, methods=['POST'], endpoint='post_%s' % resource_name)(
                post_func)
            views[_model_name]['post'] = {'url': post_url}
            if 'input_schema_modifier' in post_dict:
                views[_model_name]['post']['input_schema'] = post_dict['input_schema_modifier'](
                    deepcopy(model_schemas[_model.__name__]['input_schema']))

        if 'put' not in disabled_views:
            put_dict = view_dict_for_model.get('put', {})
            if callable(put_dict.get('input_schema_modifier')):
                put_input_schema = put_dict['input_schema_modifier'](deepcopy(model_default_input_schema))
            else:
                put_input_schema = model_default_input_schema
            put_func = put_dict.get('view_func', None) or construct_put_view_function(
                _model, put_input_schema,
                registration_dict=registration_dict,
                permitted_object_getter=put_dict.get('permitted_object_getter') or _model_dict.get('permitted_object_getter'),
                pre_processors=put_dict.get('pre_processors'),
                post_processors=put_dict.get('post_processors'),
                dict_struct=put_dict.get('dict_struct') or dict_struct_for_model,
                allow_unknown_fields=allow_unknown_fields,
                query_constructor=put_dict.get('query_constructor') or default_query_constructor,
                schemas_registry=schemas_registry,
                exception_handler=exception_handler,
                access_checker=put_dict.get('access_checker') or default_access_checker,
                fields_forbidden_from_being_set=union([
                    fields_forbidden_from_being_set_for_all_views,
                    put_dict.get('fields_forbidden_from_being_set', [])]))
            put_url = put_dict.get('url', None) or "/%s/<_id>" % base_url
            app_or_bp.route(
                put_url, methods=['PUT'], endpoint='put_%s' % resource_name)(
                put_func)
            views[_model_name]['put'] = {'url': put_url}
            if 'input_schema_modifier' in put_dict:
                views[_model_name]['put']['input_schema'] = put_dict['input_schema_modifier'](
                    deepcopy(model_schemas[_model.__name__]['input_schema']))

        # if 'batch_put' not in disabled_views:
        #     batch_put_dict = view_dict_for_model.get('batch_put', {})
        #     if callable(batch_put_dict.get('input_schema_modifier')):
        #         batch_put_input_schema = batch_put_dict['input_schema_modifier'](deepcopy(model_default_input_schema))
        #     else:
        #         batch_put_input_schema = model_default_input_schema
        #     batch_put_func = batch_put_dict.get('view_func', None) or construct_batch_put_view_function(
        #         _model, batch_put_input_schema,
        #         pre_processors=batch_put_dict.get('pre_processors'),
        #         registration_dict=registration_dict,
        #         post_processors=batch_put_dict.get('post_processors'),
        #         allow_unknown_fields=allow_unknown_fields,
        #         query_constructor=batch_put_dict.get('query_constructor') or default_query_constructor,
        #         schemas_registry=schemas_registry,
        #         exception_handler=exception_handler,
        #         fields_forbidden_from_being_set=union([
        #             fields_forbidden_from_being_set_for_all_views,
        #             batch_put_dict.get('fields_forbidden_from_being_set', [])]))
        #     batch_put_url = batch_put_dict.get('url', None) or "/%s" % base_url
        #     app_or_bp.route(
        #         batch_put_url, methods=['PUT'], endpoint='batch_put_%s' % resource_name)(
        #         batch_put_func)
        #     views[_model_name]['batch_put'] = {'url': batch_put_url}
        #     if 'input_schema_modifier' in batch_put_dict:
        #         views[_model_name]['batch_put']['input_schema'] = batch_put_dict['input_schema_modifier'](
        #             deepcopy(model_schemas[_model.__name__]['input_schema']))

        if 'patch' not in disabled_views:
            patch_dict = view_dict_for_model.get('patch', {})
            if callable(patch_dict.get('input_schema_modifier')):
                patch_input_schema = patch_dict['input_schema_modifier'](deepcopy(model_default_input_schema))
            else:
                patch_input_schema = model_default_input_schema
            patch_func = patch_dict.get('view_func', None) or construct_patch_view_function(
                _model, patch_input_schema,
                pre_processors=patch_dict.get('pre_processors'),
                processors=patch_dict.get('processors'),
                post_processors=patch_dict.get('post_processors'),
                query_constructor=patch_dict.get('query_constructor') or default_query_constructor,
                permitted_object_getter=patch_dict.get('permitted_object_getter') or _model_dict.get('permitted_object_getter'),
                schemas_registry=schemas_registry, exception_handler=exception_handler,
                access_checker=patch_dict.get('access_checker') or default_access_checker,
                dict_struct=patch_dict.get('dict_struct') or dict_struct_for_model)
            patch_url = patch_dict.get('url', None) or "/%s/<_id>" % base_url
            app_or_bp.route(
                patch_url, methods=['PATCH'], endpoint='patch_%s' % resource_name)(
                patch_func)
            views[_model_name]['patch'] = {'url': patch_url}
            if 'input_schema_modifier' in patch_dict:
                views[_model_name]['patch']['input_schema'] = patch_dict['input_schema_modifier'](
                    deepcopy(model_schemas[_model.__name__]['input_schema']))

        if 'delete' not in disabled_views:
            delete_dict = view_dict_for_model.get('delete', {})
            delete_func = delete_dict.get('view_func', None) or construct_delete_view_function(
                _model,
                query_constructor=delete_dict.get('query_constructor') or default_query_constructor,
                pre_processors=delete_dict.get('pre_processors'),
                registration_dict=registration_dict,
                permitted_object_getter=delete_dict.get('permitted_object_getter') or _model_dict.get('permitted_object_getter'),
                post_processors=delete_dict.get('post_processors'), exception_handler=exception_handler,
                access_checker=delete_dict.get('access_checker') or default_access_checker)
            delete_url = delete_dict.get('url', None) or "/%s/<_id>" % base_url
            app_or_bp.route(
                delete_url, methods=['DELETE'], endpoint='delete_%s' % resource_name)(
                delete_func)
            views[_model_name]['delete'] = {'url': delete_url}

        if 'batch_save' not in disabled_views:
            batch_save_dict = view_dict_for_model.get('batch_save', {})
            if callable(batch_save_dict.get('input_schema_modifier')):
                batch_save_input_schema = batch_save_dict['input_schema_modifier'](deepcopy(model_default_input_schema))
            else:
                batch_save_input_schema = model_default_input_schema
            batch_save_func = batch_save_dict.get('view_func', None) or construct_batch_save_view_function(
                _model, batch_save_input_schema,
                app_or_bp=app_or_bp,
                registration_dict=registration_dict,
                pre_processors_for_post=fetch_nested_key_from_dict(view_dict_for_model, 'post.pre_processors'),
                pre_processors_for_put=fetch_nested_key_from_dict(view_dict_for_model, 'put.pre_processors'),
                post_processors_for_post=fetch_nested_key_from_dict(view_dict_for_model, 'post.post_processors'),
                post_processors_for_put=fetch_nested_key_from_dict(view_dict_for_model, 'put.post_processors'),
                extra_pre_processors=batch_save_dict.get('extra_pre_processors'),
                extra_post_processors=batch_save_dict.get('extra_post_processors'),
                unique_identifier_fields=batch_save_dict.get('unique_identifier_fields'),
                dict_struct=batch_save_dict.get('dict_struct') or dict_struct_for_model,
                allow_unknown_fields=allow_unknown_fields,
                query_constructor=batch_save_dict.get('query_constructor') or default_query_constructor,
                schemas_registry=schemas_registry,
                exception_handler=exception_handler,
                tmp_folder_path=tmp_folder_path,
                fields_forbidden_from_being_set=union([
                    fields_forbidden_from_being_set_for_all_views,
                    batch_save_dict.get('fields_forbidden_from_being_set', [])]),
                celery_worker=celery_worker,
                result_saving_instance_model=batch_save_dict.get('result_saving_instance_model'),
                result_saving_instance_getter=batch_save_dict.get('result_saving_instance_getter'),
                async=batch_save_dict.get('async', False))
            batch_save_url = batch_save_dict.get('url', None) or "/batch-save/%s" % base_url
            app_or_bp.route(
                batch_save_url, methods=['POST'], endpoint='batch_save_%s' % resource_name)(
                batch_save_func)
            views[_model_name]['batch_save'] = {'url': batch_save_url}
            if 'input_schema_modifier' in batch_save_dict:
                views[_model_name]['batch_save']['input_schema'] = batch_save_dict['input_schema_modifier'](
                    deepcopy(model_schemas[_model.__name__]['input_schema']))



