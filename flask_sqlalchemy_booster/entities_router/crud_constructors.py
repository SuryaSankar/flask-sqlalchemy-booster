from __future__ import absolute_import
from flask import g, request, Response, url_for
from schemalite.core import validate_dict, validate_list_of_dicts, json_encoder
from sqlalchemy.sql import sqltypes
import json
from toolspy import (
    all_subclasses, fetch_nested_key_from_dict, fetch_nested_key,
    delete_dict_keys, union, merge, difference)
from copy import deepcopy
import inspect
import six.moves.urllib.request, six.moves.urllib.parse, six.moves.urllib.error
import functools
import csv
import traceback
from . import entity_definition_keys as edk

from ..responses import (
    as_dict, get_request_json, get_request_args,
    process_args_and_render_json_list, success_json, error_json,
    render_json_obj_with_requested_structure,
    render_json_list_with_requested_structure,
    render_dict_with_requested_structure,
    _serializable_params, serializable_obj, as_json,
    process_args_and_fetch_rows, convert_result_to_response)

from ..utils import remove_empty_values_in_dict, save_file_from_request, convert_to_proper_types

from werkzeug.exceptions import Unauthorized
from six.moves import zip

def permit_only_allowed_fields(data, fields_allowed_to_be_set=None, fields_forbidden_from_being_set=None):
    if fields_allowed_to_be_set and len(fields_allowed_to_be_set) > 0:
        for k in data.keys():
            if k not in fields_allowed_to_be_set:
                del data[k]
    if fields_forbidden_from_being_set and len(fields_forbidden_from_being_set) > 0:
        delete_dict_keys(data, fields_forbidden_from_being_set)


def construct_get_view_function(
        model_class,
        permitted_object_getter=None,
        dict_struct=None, schemas_registry=None, get_query_creator=None,
        enable_caching=False, cache_handler=None, cache_key_determiner=None,
        cache_timeout=None, exception_handler=None, access_checker=None,
        dict_post_processors=None, id_attr_name=None):

    def get(_id):
        try:
            _id = _id.strip()
            if id_attr_name:
                id_col_name = id_attr_name
            else:
                id_col_name = g.args.get('_id_attr')
            if _id.startswith('[') and _id.endswith(']'):
                # Handles multiple ids being passed
                # Eg: /tasks/[1,2,3]
                if permitted_object_getter is not None:
                    # If the endpoint is meant to allow only a particular instance to be queried,
                    # that should be returned by the permitted_object_getter function. 
                    # Typical use case is when you want to show a singleton object like current cart.
                    # If the endpoint is always meant to return current cart only, you can register the
                    # url like this - /carts/current and set the permitted_object_getter function to 
                    # return the current cart only.
                    resources = [permitted_object_getter()]
                    ids = [_id[1:-1]]
                else:
                    ids = json.loads(_id)
                    if get_query_creator:
                        resources = get_query_creator(
                            model_class.query).get_all(ids, key=id_col_name)
                    else:
                        resources = model_class.get_all(ids, key=id_col_name)
                if callable(access_checker):
                    resources = [r if access_checker(r)[0]
                                 else None for r in resources]
                if None in resources:
                    if all(r is None for r in resources):
                        status = "failure"
                    else:
                        status = "partial_success"
                else:
                    status = "success"
                return render_json_list_with_requested_structure(
                    resources,
                    pre_render_callback=lambda output_dict: {
                        'status': status,
                        'result': {
                            _id: {'status': 'failure', 'error': 'Resource not found'}
                            if obj is None
                            else {'status': 'success', 'result': obj}
                            for _id, obj in list(zip(ids, output_dict['result']))}
                    },
                    dict_struct=dict_struct,
                    dict_post_processors=dict_post_processors
                )
            if permitted_object_getter is not None:
                obj = permitted_object_getter()
            else:
                if get_query_creator:
                    id_attr = getattr(model_class, id_col_name) if id_col_name else model_class.primary_key()
                    obj = get_query_creator(model_class.query).filter(id_attr == _id).first()
                else:
                    if id_col_name:
                        obj = model_class.get(_id, key=id_col_name)
                    else:
                        obj = model_class.get(_id)
            if obj is None:
                return error_json(404, 'Resource not found')

            if callable(access_checker):
                allowed, message = access_checker(obj)
                if not allowed:
                    return error_json(401, message)
            return render_json_obj_with_requested_structure(
                obj, dict_struct=dict_struct,
                dict_post_processors=dict_post_processors)

        except Exception as e:
            if exception_handler:
                return exception_handler(e)
            traceback.print_exc()
            return error_json(400, e.message)

    if enable_caching and cache_handler is not None:
        if cache_key_determiner is None:
            def make_key_prefix(func_name):
                """Make a key that includes GET parameters."""
                args = request.args
                key = request.path + '?' + six.moves.urllib.parse.urlencode([
                    (k, v) for k in sorted(args) for v in sorted(args.getlist(k))
                ])
                # key = url_for(request.endpoint, **request.args)
                return key
            cache_key_determiner = make_key_prefix
        cached_get = cache_handler.memoize(
            timeout=cache_timeout,
            make_name=cache_key_determiner)(get)
        return cached_get
    return get


def construct_index_view_function(
        model_class, index_query_creator=None, dict_struct=None,
        enable_caching=False, cache_handler=None, cache_key_determiner=None,
        custom_response_creator=None,
        cache_timeout=None, exception_handler=None, access_checker=None,
        default_limit=None, default_sort=None, default_orderby=None,
        default_offset=None, default_page=None, default_per_page=None):
    def index():
        try:
            if callable(access_checker):
                allowed, message = access_checker()
                if not allowed:
                    return error_json(401, message)
            query_obj = model_class
            if callable(index_query_creator):
                query_obj = index_query_creator(model_class.query)
            result_rows = process_args_and_fetch_rows(
                query_obj,
                default_limit=default_limit,
                default_sort=default_sort,
                default_orderby=default_orderby,
                default_offset=default_offset,
                default_page=default_page,
                default_per_page=default_per_page)
            if custom_response_creator:
                response = custom_response_creator(result_rows)
                if isinstance(response, Response):
                    return response
            return convert_result_to_response(result_rows, dict_struct=dict_struct)

        except Exception as e:
            if exception_handler:
                return exception_handler(e)
            traceback.print_exc()
            return error_json(400, e.message)

    if enable_caching and cache_handler is not None:
        if cache_key_determiner is None:
            def make_key_prefix():
                """Make a key that includes GET parameters."""
                args = request.args
                key = request.path + '?' + six.moves.urllib.parse.urlencode([
                    (k, v) for k in sorted(args) for v in sorted(args.getlist(k))
                ])
                # key = url_for(request.endpoint, **request.args)
                return key
            cache_key_determiner = make_key_prefix
        return cache_handler.cached(
            timeout=cache_timeout, key_prefix=cache_key_determiner)(index)

    return index


def construct_post_view_function(
        model_class, schema, entities_group=None, pre_processors=None,
        post_processors=None,
        allow_unknown_fields=False,
        dict_struct=None, schemas_registry=None,
        fields_allowed_to_be_set=None,
        fields_forbidden_from_being_set=None, exception_handler=None,
        remove_relationship_keys_before_validation=False,
        remove_assoc_proxy_keys_before_validation=False,
        remove_property_keys_before_validation=False,
        access_checker=None):

    def post():
        try:
            request_json = get_request_json()
            raw_input_data = deepcopy(request_json)
            if callable(access_checker):
                allowed, message = access_checker()
                if not allowed:
                    return error_json(401, message)
            input_data = request_json
            if pre_processors is not None:
                for processor in pre_processors:
                    if callable(processor):
                        process_result = processor(data=input_data)
                        if process_result:
                            if isinstance(process_result, Response):
                                return process_result
                            if isinstance(process_result, dict):
                                input_data = process_result

            fields_to_be_removed = union([
                fields_forbidden_from_being_set or [],
                model_class._fields_forbidden_from_being_set_ or []
            ])
            if remove_property_keys_before_validation:
                fields_to_be_removed = union([
                    fields_to_be_removed, model_class.property_keys() or []
                ])
            if remove_relationship_keys_before_validation:
                fields_to_be_removed = union(
                    [fields_to_be_removed, model_class.relationship_keys() or []])
            if remove_assoc_proxy_keys_before_validation:
                fields_to_be_removed = union(
                    [fields_to_be_removed, model_class.association_proxy_keys() or []])
            if isinstance(input_data, list):
                if fields_allowed_to_be_set and len(fields_to_be_removed) > 0:
                    for dict_item in input_data:
                        permit_only_allowed_fields(
                            dict_item, fields_allowed_to_be_set=fields_allowed_to_be_set, 
                            fields_forbidden_from_being_set=fields_to_be_removed)
                # if fields_allowed_to_be_set:
                #     for dict_item in input_data:
                #         for k in dict_item.keys():
                #             if k not in fields_allowed_to_be_set:
                #                 del dict_item[k]
                # if len(fields_to_be_removed) > 0:
                #     for dict_item in input_data:
                #         delete_dict_keys(dict_item, fields_to_be_removed)
                input_data = model_class.pre_validation_adapter_for_list(
                    input_data)
                if isinstance(input_data, Response):
                    return input_data
                is_valid, errors = validate_list_of_dicts(
                    input_data, schema, context={"model_class": model_class},
                    allow_unknown_fields=allow_unknown_fields,
                    schemas_registry=schemas_registry)
                input_objs = input_data
                if not is_valid:
                    input_objs = [
                        input_obj if error is None else None
                        for input_obj, error in zip(input_data, errors)]
                resources = model_class.create_all(input_objs)
                if post_processors is not None:
                    for processor in post_processors:
                        if callable(processor):
                            processed_resources = []
                            for resource, datum in zip(resources, input_data):
                                processed_resource = processor(resource, datum)
                                if processed_resource is not None:
                                    processed_resources.append(
                                        processed_resource)
                                else:
                                    processed_resources.append(resource)
                            resources = processed_resources
                if None in resources:
                    if all(r is None for r in resources):
                        status = "failure"
                    else:
                        status = "partial_success"
                else:
                    status = "success"
                return render_json_list_with_requested_structure(
                    resources,
                    pre_render_callback=lambda output_dict: {
                        'status': status,
                        'result': [
                            {'status': 'failure', 'error': error}
                            if obj is None
                            else
                            {'status': 'success', 'result': obj}
                            for obj, error in zip(output_dict['result'], errors)]})
            else:
                permit_only_allowed_fields(
                    input_data,
                    fields_allowed_to_be_set=fields_allowed_to_be_set,
                    fields_forbidden_from_being_set=fields_to_be_removed)
                # if fields_allowed_to_be_set:
                #     for k in input_data.keys():
                #         if k not in fields_allowed_to_be_set:
                #             del input_data[k]
                # if len(fields_to_be_removed) > 0:
                #     delete_dict_keys(input_data, fields_to_be_removed)
                input_data = model_class.pre_validation_adapter(input_data)
                if isinstance(input_data, Response):
                    return input_data
                is_valid, errors = validate_dict(
                    input_data, schema, context={"model_class": model_class},
                    schemas_registry=schemas_registry,
                    allow_unknown_fields=allow_unknown_fields)
                if not is_valid:
                    return error_json(400, errors)
                obj = model_class.create(**input_data)
                if post_processors is not None:
                    for processor in post_processors:
                        if callable(processor):
                            processed_obj = processor(
                                obj, input_data,
                                raw_input_data=raw_input_data)
                            if processed_obj is not None:
                                obj = processed_obj
                request_args = get_request_args()
                if request_args and '_ret' in request_args:
                    rels = request_args['_ret'].split(".")
                    final_obj = obj
                    for rel in rels:
                        final_obj = getattr(final_obj, rel)
                    final_obj_cls = type(final_obj)
                    final_obj_dict_struct = None
                    final_obj_entity = entities_group.get_entity(final_obj_cls.__name__)
                    if final_obj_entity:
                        final_obj_dict_struct = fetch_nested_key(
                            final_obj_entity, 'get.response_dict_struct') or final_obj_entity.response_dict_struct
                    return render_json_obj_with_requested_structure(final_obj, dict_struct=final_obj_dict_struct)
                return render_json_obj_with_requested_structure(obj, dict_struct=dict_struct)
        except Exception as e:
            if exception_handler:
                return exception_handler(e)
            traceback.print_exc()
            return error_json(400, e.message)
    return post

def construct_put_view_function(
        model_class, schema,
        entities_group=None,
        pre_processors=None,
        post_processors=None,
        query_constructor=None, schemas_registry=None,
        permitted_object_getter=None,
        dict_struct=None,
        allow_unknown_fields=False,
        access_checker=None,
        fields_allowed_to_be_set=None,
        fields_forbidden_from_being_set=None, remove_relationship_keys_before_validation=False,
        remove_assoc_proxy_keys_before_validation=False,
        remove_property_keys_before_validation=False,
        exception_handler=None):
    def put(_id):
        try:
            if permitted_object_getter is not None:
                obj = permitted_object_getter()
            else:
                if callable(query_constructor):
                    obj = query_constructor(
                        model_class.query).filter(
                        model_class.primary_key()==_id).first()
                else:
                    obj = model_class.get(_id)
            if obj is None:
                return error_json(404, 'Resource not found')
            if callable(access_checker):
                allowed, message = access_checker(obj)
                if not allowed:
                    return error_json(401, message)
            request_json = get_request_json()
            raw_input_data = deepcopy(request_json)
            input_data = request_json
            if pre_processors is not None:
                for processor in pre_processors:
                    if callable(processor):
                        process_result = processor(data=input_data, existing_instance=obj)
                        if process_result:
                            if isinstance(process_result, Response):
                                return process_result
                            if isinstance(process_result, dict):
                                input_data = process_result

            fields_to_be_removed = union([
                fields_forbidden_from_being_set or [],
                model_class._fields_forbidden_from_being_set_ or []
            ])
            if remove_property_keys_before_validation:
                fields_to_be_removed = union([
                    fields_to_be_removed, model_class.property_keys() or []
                ])
            if remove_relationship_keys_before_validation:
                fields_to_be_removed = union(
                    [fields_to_be_removed, model_class.relationship_keys() or []])
            if remove_assoc_proxy_keys_before_validation:
                fields_to_be_removed = union(
                    [fields_to_be_removed, model_class.association_proxy_keys() or []])
            if len(fields_to_be_removed) > 0:
                delete_dict_keys(input_data, fields_to_be_removed)
            input_data = model_class.pre_validation_adapter(input_data, existing_instance=obj)
            if isinstance(input_data, Response):
                return input_data
            polymorphic_field = schema.get('polymorphic_on')
            if polymorphic_field:
                if polymorphic_field not in input_data:
                    input_data[polymorphic_field] = getattr(obj, polymorphic_field)
            is_valid, errors = validate_dict(
                input_data, schema, allow_required_fields_to_be_skipped=True,
                allow_unknown_fields=allow_unknown_fields,
                context={"existing_instance": obj,
                         "model_class": model_class},
                schemas_registry=schemas_registry)
            if not is_valid:
                return error_json(400, errors)
            pre_modification_data = obj.todict(dict_struct={"rels": {}})
            updated_obj = obj.update(**input_data)
            if post_processors is not None:
                for processor in post_processors:
                    if callable(processor):
                        processed_updated_obj = processor(
                            updated_obj, input_data,
                            pre_modification_data=pre_modification_data,
                            raw_input_data=raw_input_data)
                        if processed_updated_obj is not None:
                            updated_obj = processed_updated_obj
            request_args = get_request_args()
            if '_ret' in request_args:
                rels = request_args['_ret'].split(".")
                final_obj = updated_obj
                for rel in rels:
                    final_obj = getattr(final_obj, rel)
                final_obj_cls = type(final_obj)
                final_obj_dict_struct = None
                final_obj_entity = entities_group.get_entity(final_obj_cls.__name__)
                if final_obj_entity:
                    final_obj_dict_struct = fetch_nested_key(
                        final_obj_entity, 'get.response_dict_struct') or final_obj_entity.response_dict_struct
                return render_json_obj_with_requested_structure(final_obj, dict_struct=final_obj_dict_struct)
            return render_json_obj_with_requested_structure(
                updated_obj,
                dict_struct=dict_struct)
        except Exception as e:
            if exception_handler:
                return exception_handler(e)
            traceback.print_exc()
            return error_json(400, e.message)

    return put

def construct_patch_view_function(model_class, schema, pre_processors=None,
                                  query_constructor=None, schemas_registry=None,
                                  exception_handler=None, permitted_object_getter=None,
                                  commands=None, post_processors=None, access_checker=None,
                                  dict_struct=None):
    def patch(_id):
        try:
            request_json = get_request_json()
            if permitted_object_getter is not None:
                obj = permitted_object_getter()
            else:
                if callable(query_constructor):
                    obj = query_constructor(model_class.query).filter(
                        model_class.primary_key() == _id).first()
                else:
                    obj = model_class.get(_id)
            if obj is None:
                return error_json(404, 'Resource not found')
            if callable(access_checker):
                allowed, message = access_checker(obj)
                if not allowed:
                    return error_json(401, message)
            if pre_processors is not None:
                for processor in pre_processors:
                    if callable(processor):
                        processor(obj)
            cmd = request_json.get('cmd')
            if cmd in commands and callable(commands[cmd]):
                updated_obj = commands[cmd](obj, request_json)
                if isinstance(updated_obj, Response):
                    return updated_obj
            # if processors:
            #     updated_obj = obj
            #     for processor in processors:
            #         if callable(processor):
            #             updated_obj = processor(updated_obj, request_json)
            #             if isinstance(updated_obj, Response):
            #                 return updated_obj

            # else:
            #     polymorphic_field = schema.get('polymorphic_on')
            #     if polymorphic_field:
            #         if polymorphic_field not in request_json:
            #             # Why is this being done only on patch? 
            #             # If polymorphic objects can be handled by put, 
            #             # why cant they be handled in patch without setting the discriminator?
            #             request_json[polymorphic_field] = getattr(
            #                 obj, polymorphic_field)
            #     is_valid, errors = validate_dict(
            #         request_json, schema, allow_required_fields_to_be_skipped=True,
            #         context={"existing_instance": obj,
            #                  "model_class": model_class},
            #         schemas_registry=schemas_registry)
            #     if not is_valid:
            #         return error_json(400, errors)
            #     updated_obj = obj.update(**request_json)

            if post_processors is not None:
                for processor in post_processors:
                    if callable(processor):
                        processed_updated_obj = processor(updated_obj, request_json)
                        if processed_updated_obj is not None:
                            updated_obj = processed_updated_obj
            return render_json_obj_with_requested_structure(updated_obj, dict_struct=dict_struct)
        except Exception as e:
            if exception_handler:
                return exception_handler(e)
            traceback.print_exc()
            return error_json(400, e.message)

    return patch

def construct_delete_view_function(
        model_class,
        entities_group=None,
        pre_processors=None,
        post_processors=None,
        query_constructor=None,
        permitted_object_getter=None, exception_handler=None,
        access_checker=None):
    def delete(_id):
        try:
            if permitted_object_getter is not None:
                obj = permitted_object_getter()
            else:
                if callable(query_constructor):
                    obj = query_constructor(
                        model_class.query).filter(
                        model_class.primary_key() == _id).first()
                else:
                    obj = model_class.get(_id)
            if obj is None:
                return error_json(404, 'Resource not found')
            if callable(access_checker):
                allowed, message = access_checker(obj)
                if not allowed:
                    return error_json(401, message)
            if pre_processors is not None:
                for processor in pre_processors:
                    if callable(processor):
                        processor(obj)
            obj_data = obj.todict()

            rel_obj_requested_in_return = None
            request_args = get_request_args()
            if '_ret' in request_args:
                rels = request_args['_ret'].split(".")
                if len(rels) > 0:
                    rel_obj_requested_in_return = obj
                    for rel in rels:
                        rel_obj_requested_in_return = getattr(
                            rel_obj_requested_in_return, rel)

            obj.delete()
            if post_processors is not None:
                for processor in post_processors:
                    if callable(processor):
                        processor(obj_data)

            if rel_obj_requested_in_return is not None:
                cls_of_rel_obj_requested_in_return = type(
                    rel_obj_requested_in_return)
                rel_obj_dict_struct = None
                refetched_rel_obj = cls_of_rel_obj_requested_in_return.get(
                    rel_obj_requested_in_return.primary_key_value())

                rel_obj_entity = entities_group.get_entity(cls_of_rel_obj_requested_in_return.__name__)
                if rel_obj_entity:
                    rel_obj_dict_struct = fetch_nested_key(
                        rel_obj_entity, 'get.response_dict_struct') or rel_obj_entity.response_dict_struct

                return render_json_obj_with_requested_structure(
                    refetched_rel_obj, dict_struct=rel_obj_dict_struct)

            return success_json()
        except Exception as e:
            if exception_handler:
                return exception_handler(e)
            traceback.print_exc()
            return error_json(400, e.message)
    return delete


def get_result_dict_from_response(rsp):
    response = rsp.response
    if isinstance(response, list) and len(response) > 0:
        return json.loads(response[0])
    return None


def construct_batch_save_view_function(
        model_class, schema, app_or_bp=None,
        pre_processors_for_post=None, pre_processors_for_put=None,
        post_processors_for_post=None, post_processors_for_put=None,
        extra_pre_processors=None,
        extra_post_processors=None,
        unique_identifier_fields=None,
        query_constructor=None, schemas_registry=None,
        dict_struct=None,
        allow_unknown_fields=False,
        access_checker=None,
        fields_forbidden_from_being_set=None, exception_handler=None,
        tmp_folder_path="/tmp", celery_worker=None,
        result_saving_instance_model=None,
        result_saving_instance_getter=None,
        run_as_async_task=False,
        update_only=False, create_only=False,
        skip_pre_processors=False, skip_post_processors=False):

    def determine_response_for_input_row(
            input_row, existing_instance, raw_input_row,
            result_saving_instance=None, update_only=False, create_only=False,
            skip_pre_processors=False, skip_post_processors=False):
        if existing_instance and create_only:
            return {
                "status": "failure",
                "code": 401,
                "error": "Cannot create a new instance as a matching instance is existing",
                "input": raw_input_row
            }
        if not existing_instance and update_only:
            return {
                "status": "failure",
                "code": 404,
                "error": "No matching instance found",
                "input": raw_input_row
            }
        if existing_instance and callable(access_checker):
            allowed, message = access_checker(existing_instance)
            if not allowed:
                return {
                    "status": "failure",
                    "code": 401,
                    "error": message,
                    "input": raw_input_row
                }
        if not skip_pre_processors:
            pre_processors = pre_processors_for_put if existing_instance else pre_processors_for_post
            if pre_processors is not None:
                for pre_processor in pre_processors:
                    if callable(pre_processor):
                        process_result = pre_processor(
                            data=input_row, existing_instance=existing_instance,
                            extra_params={"result_saving_instance_id": fetch_nested_key(result_saving_instance, 'id')})
                        if process_result and isinstance(process_result, Response):
                            response = get_result_dict_from_response(
                                process_result)
                            if response:
                                return merge(response, {"input": raw_input_row})

        modified_input_row = model_class.pre_validation_adapter(
            input_row, existing_instance)
        if isinstance(modified_input_row, Response):
            response = get_result_dict_from_response(modified_input_row)
            if response:
                return merge(response, {"input": raw_input_row})
        input_row = modified_input_row

        polymorphic_field = schema.get('polymorphic_on')
        if polymorphic_field:
            if polymorphic_field not in input_row:
                input_row[polymorphic_field] = getattr(
                    existing_instance, polymorphic_field)
        is_valid, errors = validate_dict(
            input_row, schema, allow_required_fields_to_be_skipped=True,
            allow_unknown_fields=allow_unknown_fields,
            context={"existing_instance": existing_instance,
                     "model_class": model_class},
            schemas_registry=schemas_registry)
        if not is_valid:
            return {
                "status": "failure",
                "code": 401,
                "error": errors,
                "input": raw_input_row
            }

        pre_modification_data = existing_instance.todict(
            dict_struct={"rels": {}}) if existing_instance else None
        obj = existing_instance.update(
            **input_row) if existing_instance else model_class.create(**input_row)
        if not skip_post_processors:
            post_processors = post_processors_for_put if existing_instance else post_processors_for_post
            if post_processors is not None:
                for processor in post_processors:
                    if callable(processor):
                        processed_obj = processor(
                            obj, input_row,
                            extra_params={
                                "pre_modification_data": pre_modification_data,
                                "raw_input_data": raw_input_row
                            },
                            pre_modification_data=pre_modification_data,
                            raw_input_data=raw_input_row)
                        if processed_obj is not None:
                            obj = processed_obj
        return merge(
            as_dict(obj, dict_struct=dict_struct),
            {"input": raw_input_row}
        )

    def process_batch_input_data(
            input_data, result_saving_instance=None, update_only=False, create_only=False,
            skip_pre_processors=False, skip_post_processors=False):

        raw_input_data = deepcopy(input_data)

        fields_to_be_removed = union([
            fields_forbidden_from_being_set or [],
            model_class._fields_forbidden_from_being_set_ or []
        ])
        if len(fields_to_be_removed) > 0:
            for dict_item in input_data:
                delete_dict_keys(dict_item, fields_to_be_removed)

        if extra_pre_processors:
            for pre_processor in extra_pre_processors:
                if callable(pre_processor):
                    input_data = [pre_processor(row) for row in input_data]

        primary_key_name = model_class.primary_key_name()
        obj_ids = [obj.get(primary_key_name) for obj in input_data]
        existing_instances = model_class.get_all(obj_ids)

        # Identifying which instance to update using some other key apart from the primary key
        if unique_identifier_fields:
            for idx, input_row in enumerate(input_data):
                existing_instance = existing_instances[idx]
                if existing_instance is None:
                    if all(input_row.get(f) is not None for f in unique_identifier_fields):
                        filter_kwargs = {f: input_row.get(
                            f) for f in unique_identifier_fields}
                        existing_instances[idx] = model_class.query.filter_by(
                            **filter_kwargs).first()
                        if existing_instances[idx]:
                            # Setting the primary key value in the dict so that the
                            # corresponding instance would be updated
                            input_row[primary_key_name] = getattr(
                                existing_instances[idx], primary_key_name)

        if callable(access_checker):
            allowed, message = access_checker()
            if not allowed:
                raise Unauthorized(message, error_json(401, message))
                # return error_json(401, message)

        output_objs = []
        errors = []

        responses = []

        for input_row, existing_instance, raw_input_row in zip(input_data, existing_instances, raw_input_data):
            try:
                responses.append(
                    determine_response_for_input_row(
                        input_row, existing_instance, raw_input_row,
                        result_saving_instance=result_saving_instance,
                        update_only=update_only, create_only=create_only,
                        skip_pre_processors=skip_pre_processors,
                        skip_post_processors=skip_post_processors))
            except Exception as e:
                responses.append({
                    "status": "failure",
                    "code": 400,
                    "error": e.message
                })

        status = "success"

        consolidated_result = {
            "status": status,
            "result": responses
        }
        return consolidated_result

    def async_process_batch_input_data(
            input_data, result_saving_instance_id=None,
            update_only=False, create_only=False,
            skip_pre_processors=False, skip_post_processors=False):
        try:
            result_saving_instance = None
            if result_saving_instance_id and result_saving_instance_model:
                result_saving_instance = result_saving_instance_model.get(
                    result_saving_instance_id)
            if result_saving_instance:
                result_saving_instance.mark_as_started()
                # result_saving_instance.pre_process_input_data(input_data)
            response = process_batch_input_data(
                input_data, result_saving_instance,
                update_only=update_only, create_only=create_only,
                skip_pre_processors=skip_pre_processors,
                skip_post_processors=skip_post_processors)
            if result_saving_instance:
                result_saving_instance.save_response_data(response)
        except Exception as e:
            result_saving_instance.record_exception(e)
            if exception_handler:
                return exception_handler(e)

    if celery_worker and run_as_async_task:
        async_process_batch_input_data = celery_worker.task(name="crud_{0}_bs_{1}".format(
            app_or_bp.name, model_class.__tablename__))(async_process_batch_input_data)

    def batch_save():

        data_file_path = None
        saving_model_instance = None
        _update_only = update_only
        _create_only = create_only
        _skip_pre_processors = skip_pre_processors
        _skip_post_processors = skip_post_processors
        if request.headers['Content-Type'].startswith("multipart/form-data"):
            data_file_path = save_file_from_request(
                request.files['file'], location=tmp_folder_path)
            with open(data_file_path) as csv_file:
                csv_reader = csv.DictReader(csv_file)
                rows = [r for r in csv_reader]
                rows = [convert_to_proper_types(
                    remove_empty_values_in_dict(row),
                    model_class) for row in rows]
                input_data = rows
            if request.form:
                _update_only = request.form.get('update_only') or update_only
                _create_only = request.form.get('create_only') or update_only
                _skip_pre_processors = request.form.get('skip_pre_processors') or skip_pre_processors
                _skip_post_processors = request.form.get('skip_post_processors') or skip_post_processors
        else:
            input_data = get_request_json()

        if run_as_async_task:
            result_saving_instance = result_saving_instance_getter(
                input_data=input_data, input_file_path=data_file_path) if callable(result_saving_instance_getter) else None
            async_process_batch_input_data.delay(
                input_data, result_saving_instance_id=result_saving_instance.id,
                update_only=_update_only, create_only=_create_only,
                skip_pre_processors=_skip_pre_processors,
                skip_post_processors=_skip_post_processors)
            if result_saving_instance:
                return render_json_obj_with_requested_structure(result_saving_instance)
            else:
                return success_json()

        # if saving_model:
        #     saving_model_instance = saving_model.create()

        # if async and celery_worker:
        #     if file_uploader:
        #         data_file_url=file_uploader(data_file_path)
        #     async_process_batch_input_data.delay(input_data, data_file_url, saving_model_instance)
        #     return success_json()
        else:
            try:
                consolidated_result = process_batch_input_data(
                    input_data, update_only=_update_only, create_only=_create_only,
                    skip_pre_processors=_skip_pre_processors,
                    skip_post_processors=_skip_post_processors)
            except Unauthorized as e:
                return error_json(401, e.description)

            return as_json(consolidated_result, wrap=False)

    return batch_save
    
