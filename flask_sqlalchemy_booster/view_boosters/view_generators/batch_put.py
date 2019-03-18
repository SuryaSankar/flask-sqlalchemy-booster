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