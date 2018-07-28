from flask.views import MethodView
from flask import g, request, Response,url_for
from schemalite import SchemaError
from schemalite.core import validate_object, validate_list_of_objects, json_encoder
from sqlalchemy.sql import sqltypes
import json
from toolspy import (
    all_subclasses, fetch_nested_key_from_dict,
    delete_dict_keys, union, merge)
from copy import deepcopy
import inspect
from .responses import (
    process_args_and_render_json_list, success_json, error_json,
    render_json_obj_with_requested_structure,
    render_json_list_with_requested_structure,
    render_dict_with_requested_structure,
    _serializable_params, serializable_obj, as_json,
    process_args_and_fetch_rows, convert_result_to_response)
import urllib
import functools
from .utils import remove_empty_values_in_dict, save_file_from_request, convert_to_proper_types
import csv


def construct_get_view_function(
        model_class, registration_dict,
        permitted_object_getter=None,
        dict_struct=None, schemas_registry=None, get_query_creator=None,
        enable_caching=False, cache_handler=None, cache_key_determiner=None,
        cache_timeout=None, exception_handler=None, access_checker=None,
        dict_post_processors=None):

    def get(_id):
        try:
            _id = _id.strip()
            if _id.startswith('[') and _id.endswith(']'):
                if permitted_object_getter is not None:
                    resources = [permitted_object_getter()]
                    ids = [_id[1:-1]]
                else:
                    ids = [int(i) for i in json.loads(_id)]
                    if get_query_creator:
                        resources = get_query_creator(model_class.query).get_all(ids)
                    else:
                        resources = model_class.get_all(ids)
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
                            for _id, obj in zip(ids, output_dict['result'])}
                    },
                    dict_struct=dict_struct,
                    dict_post_processors=dict_post_processors
                )
            if permitted_object_getter is not None:
                obj = permitted_object_getter()
            else:
                if get_query_creator:
                    obj = get_query_creator(model_class.query).filter(
                        model_class.primary_key()==_id).first()
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
            return error_json(400, e.message)

    if enable_caching and cache_handler is not None:
        if cache_key_determiner is None:
            def make_key_prefix(func_name):
                """Make a key that includes GET parameters."""
                args = request.args
                key = request.path + '?' + urllib.urlencode([
                    (k, v) for k in sorted(args) for v in sorted(args.getlist(k))
                ])
                # key = url_for(request.endpoint, **request.args)
                print "cache key ", key
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
            return error_json(400, e.message)

    if enable_caching and cache_handler is not None:
        if cache_key_determiner is None:
            def make_key_prefix():
                """Make a key that includes GET parameters."""
                args = request.args
                key = request.path + '?' + urllib.urlencode([
                    (k, v) for k in sorted(args) for v in sorted(args.getlist(k))
                ])
                # key = url_for(request.endpoint, **request.args)
                return key
            cache_key_determiner = make_key_prefix
        return cache_handler.cached(
            timeout=cache_timeout, key_prefix=cache_key_determiner)(index)

    return index


def construct_post_view_function(
        model_class, schema, registration_dict, pre_processors=None,
        post_processors=None,
        allow_unknown_fields=False,
        dict_struct=None, schemas_registry=None,
        fields_forbidden_from_being_set=None, exception_handler=None,
        access_checker=None):

    def post():
        try:
            if callable(access_checker):
                allowed, message = access_checker()
                if not allowed:
                    return error_json(401, message)
            if pre_processors is not None:
                for processor in pre_processors:
                    if callable(processor):
                        process_result = processor()
                        if process_result and isinstance(process_result, Response):
                            return process_result
            fields_to_be_removed = union([
                fields_forbidden_from_being_set or [],
                model_class._fields_forbidden_from_being_set_ or []])
            if isinstance(g.json, list):
                if len(fields_to_be_removed) > 0:
                    for dict_item in g.json:
                        delete_dict_keys(dict_item, fields_to_be_removed)
                input_data = model_class.pre_validation_adapter_for_list(g.json)
                if isinstance(input_data, Response):
                    return input_data
                is_valid, errors = validate_list_of_objects(
                    schema, input_data, context={"model_class": model_class},
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
                                    processed_resources.append(processed_resource)
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
                raw_input_data = deepcopy(g.json)
                if len(fields_to_be_removed) > 0:
                    delete_dict_keys(g.json, fields_to_be_removed)
                input_data = model_class.pre_validation_adapter(g.json)
                if isinstance(input_data, Response):
                    return input_data
                is_valid, errors = validate_object(
                    schema, input_data, context={"model_class": model_class},
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
                if '_ret' in g.args:
                    rels = g.args['_ret'].split(".")
                    final_obj = obj
                    for rel in rels:
                        final_obj = getattr(final_obj, rel)
                    final_obj_cls = type(final_obj)
                    final_obj_dict_struct = None
                    if final_obj_cls in registration_dict:
                        final_obj_dict_struct = (fetch_nested_key_from_dict(
                            registration_dict[final_obj_cls], 'views.get.dict_struct') or
                            registration_dict[final_obj_cls].get('dict_struct'))
                    return render_json_obj_with_requested_structure(final_obj, dict_struct=final_obj_dict_struct)
                return render_json_obj_with_requested_structure(obj, dict_struct=dict_struct)
        except Exception as e:
            if exception_handler:
                return exception_handler(e)
            return error_json(400, e.message)
    return post


def construct_put_view_function(
        model_class, schema,
        registration_dict=None,
        pre_processors=None,
        post_processors=None,
        query_constructor=None, schemas_registry=None,
        permitted_object_getter=None,
        dict_struct=None,
        allow_unknown_fields=False,
        access_checker=None,
        fields_forbidden_from_being_set=None, exception_handler=None):
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
            raw_input_data = deepcopy(g.json)
            if pre_processors is not None:
                for processor in pre_processors:
                    if callable(processor):
                        process_result = processor(obj)
                        if process_result and isinstance(process_result, Response):
                            return process_result
            fields_to_be_removed = union([
                fields_forbidden_from_being_set or [],
                model_class._fields_forbidden_from_being_set_ or []])
            if len(fields_to_be_removed) > 0:
                delete_dict_keys(g.json, fields_to_be_removed)
            input_data = model_class.pre_validation_adapter(g.json, existing_instance=obj)
            if isinstance(input_data, Response):
                return input_data
            polymorphic_field = schema.get('polymorphic_on')
            if polymorphic_field:
                if polymorphic_field not in input_data:
                    input_data[polymorphic_field] = getattr(obj, polymorphic_field)
            is_valid, errors = validate_object(
                schema, input_data, allow_required_fields_to_be_skipped=True,
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
            if '_ret' in g.args:
                rels = g.args['_ret'].split(".")
                final_obj = updated_obj
                for rel in rels:
                    final_obj = getattr(final_obj, rel)
                final_obj_cls = type(final_obj)
                final_obj_dict_struct = None
                if final_obj_cls in registration_dict:
                    final_obj_dict_struct = (fetch_nested_key_from_dict(
                        registration_dict[final_obj_cls], 'views.get.dict_struct') or
                        registration_dict[final_obj_cls].get('dict_struct'))
                return render_json_obj_with_requested_structure(final_obj, dict_struct=final_obj_dict_struct)
            return render_json_obj_with_requested_structure(
                updated_obj,
                dict_struct=dict_struct)
        except Exception as e:
            if exception_handler:
                return exception_handler(e)
            return error_json(400, e.message)

    return put


def construct_batch_put_view_function(
        model_class, schema, registration_dict=None,
        pre_processors=None,
        post_processors=None,
        query_constructor=None, schemas_registry=None,
        allow_unknown_fields=False,
        fields_forbidden_from_being_set=None,
        exception_handler=None):

    def batch_put():
        try:
            if pre_processors is not None:
                for processor in pre_processors:
                    if callable(processor):
                        processor()
            fields_to_be_removed = union([
                fields_forbidden_from_being_set or [],
                model_class._fields_forbidden_from_being_set_ or []])
            if len(fields_to_be_removed) > 0:
                for dict_item in g.json.values():
                    delete_dict_keys(dict_item, fields_to_be_removed)
            output = {}
            obj_ids = g.json.keys()
            if type(model_class.primary_key().type)==sqltypes.Integer:
                obj_ids = [int(obj_id) for obj_id in obj_ids]
            if callable(query_constructor):
                objs = query_constructor(model_class.query).get_all(obj_ids)
            else:
                objs = model_class.get_all(obj_ids)
            existing_instances = dict(zip(obj_ids, objs))
            all_success = True
            any_success = False
            polymorphic_field = schema.get('polymorphic_on')
            input_data = model_class.pre_validation_adapter_for_mapped_collection(g.json, existing_instances)
            if isinstance(input_data, Response):
                return input_data
            updated_objects = {}
            for obj_id, put_data_for_obj in input_data.items():
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
                    if polymorphic_field:
                        if polymorphic_field not in put_data_for_obj:
                            put_data_for_obj[polymorphic_field] = getattr(existing_instance, polymorphic_field)
                    is_valid, errors = validate_object(
                        schema, put_data_for_obj, allow_required_fields_to_be_skipped=True,
                        allow_unknown_fields=allow_unknown_fields,
                        context={
                            "existing_instance": existing_instance,
                            "model_class": model_class
                        }, schemas_registry=schemas_registry)
                    if is_valid:
                        updated_object = existing_instance.update_without_commit(
                            **put_data_for_obj)
                        if post_processors is not None:
                            for processor in post_processors:
                                if callable(processor):
                                    processed_updated_object = processor(updated_object, put_data_for_obj)
                                    if processed_updated_object is not None:
                                        updated_object = processed_updated_object
                        updated_objects[updated_object.id] = updated_object
                        output[output_key] = {
                            "status": "success",
                            "result": serializable_obj(
                                updated_object,
                                **_serializable_params(request.args))
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
            }, wrap=False)
        except Exception as e:
            if exception_handler:
                return exception_handler(e)
            return error_json(400, e.message)
    return batch_put


def construct_patch_view_function(model_class, schema, pre_processors=None,
                                  query_constructor=None, schemas_registry=None,
                                  exception_handler=None, permitted_object_getter=None,
                                  processors=None, post_processors=None, access_checker=None,
                                  dict_struct=None):
    def patch(_id):
        try:
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
            if processors:
                updated_obj = obj
                for processor in processors:
                    if callable(processor):
                        updated_obj = processor(updated_obj, g.json)
                        if isinstance(updated_obj, Response):
                            return updated_obj

            else:
                polymorphic_field = schema.get('polymorphic_on')
                if polymorphic_field:
                    if polymorphic_field not in g.json:
                        g.json[polymorphic_field] = getattr(obj, polymorphic_field)
                is_valid, errors = validate_object(
                    schema, g.json, allow_required_fields_to_be_skipped=True,
                    context={"existing_instance": obj,
                             "model_class": model_class},
                    schemas_registry=schemas_registry)
                if not is_valid:
                    return error_json(400, errors)
                updated_obj = obj.update(**g.json)

            if post_processors is not None:
                for processor in post_processors:
                    if callable(processor):
                        processed_updated_obj = processor(updated_obj, g.json)
                        if processed_updated_obj is not None:
                            updated_obj = processed_updated_obj
            return render_json_obj_with_requested_structure(updated_obj, dict_struct=dict_struct)
        except Exception as e:
            if exception_handler:
                return exception_handler(e)
            return error_json(400, e.message)

    return patch


def construct_delete_view_function(
        model_class,
        registration_dict=None,
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
                        model_class.primary_key()==_id).first()
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
            if '_ret' in g.args:
                rels = g.args['_ret'].split(".")
                if len(rels) > 0:
                    rel_obj_requested_in_return = obj
                    for rel in rels:
                        rel_obj_requested_in_return = getattr(rel_obj_requested_in_return, rel)

            obj.delete()
            if post_processors is not None:
                for processor in post_processors:
                    if callable(processor):
                        processor(obj_data)

            if rel_obj_requested_in_return is not None:
                cls_of_rel_obj_requested_in_return = type(rel_obj_requested_in_return)
                rel_obj_dict_struct = None
                refetched_rel_obj = cls_of_rel_obj_requested_in_return.get(
                    rel_obj_requested_in_return.primary_key_value())
                if cls_of_rel_obj_requested_in_return in registration_dict:
                    rel_obj_dict_struct = (fetch_nested_key_from_dict(
                        registration_dict[cls_of_rel_obj_requested_in_return], 'views.get.dict_struct') or
                        registration_dict[cls_of_rel_obj_requested_in_return].get('dict_struct'))
                return render_json_obj_with_requested_structure(
                    refetched_rel_obj, dict_struct=rel_obj_dict_struct)

            return success_json()
        except Exception as e:
            if exception_handler:
                return exception_handler(e)
            return error_json(400, e.message)
    return delete

def get_result_dict_from_response(rsp):
    response = rsp.response
    if isinstance(response, list) and len(response) > 0:
        return json.loads(response[0])
    return None


def construct_batch_save_view_function(
        model_class, schema,
        registration_dict=None,
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
        tmp_folder_path="/tmp"):
    def batch_save():
        # print "in batch save function"
        # print request.headers
        if request.headers['Content-Type'].startswith("multipart/form-data"):
            # print "Received file upload"
            csv_file_path = save_file_from_request(
                request.files['file'], location=tmp_folder_path)
            with open(csv_file_path) as csv_file:
                csv_reader = csv.DictReader(csv_file)
                rows = [r for r in csv_reader]
                rows = [convert_to_proper_types(
                    remove_empty_values_in_dict(row),
                    model_class) for row in rows]
                input_data = rows
        else:
            input_data = g.json

        raw_input_data = deepcopy(input_data)


        fields_to_be_removed = union([
            fields_forbidden_from_being_set or [],
            model_class._fields_forbidden_from_being_set_ or []])
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

        if unique_identifier_fields:
            for idx, input_row in enumerate(input_data):
                existing_instance = existing_instances[idx]
                if existing_instance is None:
                    if all(input_row.get(f) is not None for f in unique_identifier_fields):
                        filter_kwargs = {f: input_row.get(f) for f in unique_identifier_fields}
                        existing_instances[idx] = model_class.query.filter_by(**filter_kwargs).first()
                        if existing_instances[idx]:
                            input_row[primary_key_name] = getattr(
                                existing_instances[idx], primary_key_name)

        if callable(access_checker):
            allowed, message = access_checker()
            if not allowed:
                return error_json(401, message)

        output_objs = []
        errors = []

        responses = []

        for input_row, existing_instance, raw_input_row in zip(input_data, existing_instances, raw_input_data):
            # print
            # print "INPUT ", input_row
            # print "CURRENT INSTANCE ", existing_instance
            if existing_instance and callable(access_checker):
                allowed, message = access_checker(existing_instance)
                if not allowed:
                    responses.append({
                        "status": "failure",
                        "code": 401,
                        "error": message,
                        "input": raw_input_row
                    })
                    continue

            pre_processors = pre_processors_for_put if existing_instance else pre_processors_for_post
            if pre_processors is not None:
                for pre_processor in pre_processors:
                    if callable(pre_processor):
                        process_result = pre_processor(existing_instance)
                        if process_result and isinstance(process_result, Response):
                            response = get_result_dict_from_response(process_result)
                            if response:
                                responses.append(
                                    merge(response, {"input": raw_input_row})
                                )
                                continue

            modified_input_row = model_class.pre_validation_adapter(input_row, existing_instance)
            if isinstance(modified_input_row, Response):
                response = get_result_dict_from_response(modified_input_row)
                if response:
                    responses.append(merge(response, {"input": raw_input_row}))
                    continue
            input_row = modified_input_row

            polymorphic_field = schema.get('polymorphic_on')
            if polymorphic_field:
                if polymorphic_field not in input_row:
                    input_row[polymorphic_field] = getattr(existing_instance, polymorphic_field)
            is_valid, errors = validate_object(
                schema, input_row, allow_required_fields_to_be_skipped=True,
                allow_unknown_fields=allow_unknown_fields,
                context={"existing_instance": existing_instance,
                         "model_class": model_class},
                schemas_registry=schemas_registry)
            if not is_valid:
                responses.append({
                        "status": "failure",
                        "code": 401,
                        "error": errors,
                        "input": raw_input_row
                    })
                continue
            pre_modification_data = existing_instance.todict(dict_struct={"rels": {}}) if existing_instance else None
            obj = existing_instance.update(**input_row) if existing_instance else model_class.create(**input_row)

            post_processors = post_processors_for_put if existing_instance else post_processors_for_post
            if post_processors is not None:
                for processor in post_processors:
                    if callable(processor):
                        processed_obj = processor(
                            obj, input_row,
                            pre_modification_data=pre_modification_data,
                            raw_input_data=raw_input_row)
                        if processed_obj is not None:
                            obj = processed_obj

            responses.append(
                merge(
                    render_dict_with_requested_structure(obj, dict_struct=dict_struct),
                    {"input": raw_input_row}
                )
            )

        status = "success"

        consolidated_result = {
            "status": status,
            "result": responses
        }
        return as_json(consolidated_result, wrap=False)

    return batch_save


def register_crud_routes_for_models(
        app_or_bp, registration_dict, register_schema_structure=True,
        allow_unknown_fields=False, cache_handler=None, exception_handler=None,
        tmp_folder_path="/tmp"):
    if not hasattr(app_or_bp, "registered_models_and_crud_routes"):
        app_or_bp.registered_models_and_crud_routes = {
            "models_registered_for_views": [],
            "model_schemas": {

            },
            "views": {

            }
        }
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
        forbidden_views = _model_dict.get('forbidden_views', [])
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

        if 'index' not in forbidden_views:
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

        if 'get' not in forbidden_views:
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

        if 'post' not in forbidden_views:
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

        if 'put' not in forbidden_views:
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

        if 'batch_put' not in forbidden_views:
            batch_put_dict = view_dict_for_model.get('batch_put', {})
            if callable(batch_put_dict.get('input_schema_modifier')):
                batch_put_input_schema = batch_put_dict['input_schema_modifier'](deepcopy(model_default_input_schema))
            else:
                batch_put_input_schema = model_default_input_schema
            batch_put_func = batch_put_dict.get('view_func', None) or construct_batch_put_view_function(
                _model, batch_put_input_schema,
                pre_processors=batch_put_dict.get('pre_processors'),
                registration_dict=registration_dict,
                post_processors=batch_put_dict.get('post_processors'),
                allow_unknown_fields=allow_unknown_fields,
                query_constructor=batch_put_dict.get('query_constructor') or default_query_constructor,
                schemas_registry=schemas_registry,
                exception_handler=exception_handler,
                fields_forbidden_from_being_set=union([
                    fields_forbidden_from_being_set_for_all_views,
                    batch_put_dict.get('fields_forbidden_from_being_set', [])]))
            batch_put_url = batch_put_dict.get('url', None) or "/%s" % base_url
            app_or_bp.route(
                batch_put_url, methods=['PUT'], endpoint='batch_put_%s' % resource_name)(
                batch_put_func)
            views[_model_name]['batch_put'] = {'url': batch_put_url}
            if 'input_schema_modifier' in batch_put_dict:
                views[_model_name]['batch_put']['input_schema'] = batch_put_dict['input_schema_modifier'](
                    deepcopy(model_schemas[_model.__name__]['input_schema']))

        if 'patch' not in forbidden_views:
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

        if 'delete' not in forbidden_views:
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

        if 'batch_save' not in forbidden_views:
            batch_save_dict = view_dict_for_model.get('batch_save', {})
            if callable(batch_save_dict.get('input_schema_modifier')):
                batch_save_input_schema = batch_save_dict['input_schema_modifier'](deepcopy(model_default_input_schema))
            else:
                batch_save_input_schema = model_default_input_schema
            batch_save_func = batch_save_dict.get('view_func', None) or construct_batch_save_view_function(
                _model, batch_save_input_schema,
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
                    batch_save_dict.get('fields_forbidden_from_being_set', [])]))
            batch_save_url = batch_save_dict.get('url', None) or "/batch-save/%s" % base_url
            app_or_bp.route(
                batch_save_url, methods=['POST'], endpoint='batch_save_%s' % resource_name)(
                batch_save_func)
            views[_model_name]['batch_save'] = {'url': batch_save_url}
            if 'input_schema_modifier' in batch_save_dict:
                views[_model_name]['batch_save']['input_schema'] = batch_save_dict['input_schema_modifier'](
                    deepcopy(model_schemas[_model.__name__]['input_schema']))



## TO BE DEPRECATED


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
            _id = _id.strip()
            if _id.startswith('[') and _id.endswith(']'):
                ids = [int(i) for i in json.loads(_id)]
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