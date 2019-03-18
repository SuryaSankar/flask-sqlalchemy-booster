def construct_post_view_function(
        model_class, schema, registration_dict, pre_processors=None,
        post_processors=None,
        allow_unknown_fields=False,
        dict_struct=None, schemas_registry=None,
        fields_allowed_to_be_set=None,
        fields_forbidden_from_being_set=None, exception_handler=None,
        access_checker=None):

    def post():
        try:
            raw_input_data = deepcopy(g.json)
            if callable(access_checker):
                allowed, message = access_checker()
                if not allowed:
                    return error_json(401, message)
            input_data = g.json
            if pre_processors is not None:
                for processor in pre_processors:
                    if callable(processor):
                        process_result = processor(data=input_data)
                        if process_result and isinstance(process_result, Response):
                            return process_result


            fields_to_be_removed = union([
                fields_forbidden_from_being_set or [],
                model_class._fields_forbidden_from_being_set_ or []])
            if isinstance(input_data, list):
                if fields_allowed_to_be_set and len(fields_to_be_removed) > 0:
                    for dict_item in input_data:
                        permit_only_allowed_fields(
                            dict_item, fields_allowed_to_be_set=fields_allowed_to_be_set, fields_forbidden_from_being_set=fields_to_be_removed)
                # if fields_allowed_to_be_set:
                #     for dict_item in input_data:
                #         for k in dict_item.keys():
                #             if k not in fields_allowed_to_be_set:
                #                 del dict_item[k]
                # if len(fields_to_be_removed) > 0:
                #     for dict_item in input_data:
                #         delete_dict_keys(dict_item, fields_to_be_removed)
                input_data = model_class.pre_validation_adapter_for_list(input_data)
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
                if g.args and '_ret' in g.args:
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