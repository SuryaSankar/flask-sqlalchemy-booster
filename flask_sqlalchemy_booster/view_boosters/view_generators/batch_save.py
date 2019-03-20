import json
from toolspy import fetch_nested_key, merge, delete_dict_keys, union
from flask import Response, request
from schemalite.core import validate_object
from copy import deepcopy
from ..responses import as_dict, error_json
from werkzeug.exceptions import Unauthorized
from ...utils import save_file_from_request


def get_result_dict_from_response(rsp):
    response = rsp.response
    if isinstance(response, list) and len(response) > 0:
        return json.loads(response[0])
    return None


def construct_batch_save_view_function(
        model_class, schema, app_or_bp=None,
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
        tmp_folder_path="/tmp", celery_worker=None,
        result_saving_instance_model=None,
        result_saving_instance_getter=None,
        async=False):

    def determine_response_for_input_row(
            input_row, existing_instance, raw_input_row,
            result_saving_instance=None):
        if existing_instance and callable(access_checker):
            allowed, message = access_checker(existing_instance)
            if not allowed:
                return {
                    "status": "failure",
                    "code": 401,
                    "error": message,
                    "input": raw_input_row
                }

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
        is_valid, errors = validate_object(
            schema, input_row, allow_required_fields_to_be_skipped=True,
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
        return merge(
            as_dict(obj, dict_struct=dict_struct),
            {"input": raw_input_row}
        )

    def process_batch_input_data(input_data, result_saving_instance):

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
                        filter_kwargs = {f: input_row.get(
                            f) for f in unique_identifier_fields}
                        existing_instances[idx] = model_class.query.filter_by(
                            **filter_kwargs).first()
                        if existing_instances[idx]:
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
                        result_saving_instance=result_saving_instance))
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

    def async_process_batch_input_data(input_data, result_saving_instance_id=None):
        try:
            result_saving_instance = None
            if result_saving_instance_id and result_saving_instance_model:
                result_saving_instance = result_saving_instance_model.get(
                    result_saving_instance_id)
            if result_saving_instance:
                result_saving_instance.mark_as_started()
                # result_saving_instance.pre_process_input_data(input_data)
            response = process_batch_input_data(
                input_data, result_saving_instance)
            if result_saving_instance:
                result_saving_instance.save_response_data(response)
        except Exception as e:
            result_saving_instance.record_exception(e)
            if exception_handler:
                return exception_handler(e)

    if celery_worker and async:
        async_process_batch_input_data = celery_worker.task(name="crud_{0}_bs_{1}".format(
            app_or_bp.name, model_class.__tablename__))(async_process_batch_input_data)

    def batch_save():

        data_file_path = None
        saving_model_instance = None
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
        else:
            input_data = g.json

        if async:
            result_saving_instance = result_saving_instance_getter(
                input_data=input_data, input_file_path=data_file_path) if callable(result_saving_instance_getter) else None
            async_process_batch_input_data.delay(
                input_data, result_saving_instance_id=result_saving_instance.id)
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
                consolidated_result = process_batch_input_data(input_data)
            except Unauthorized as e:
                return error_json(401, e.description)

            return as_json(consolidated_result, wrap=False)

    return batch_save
