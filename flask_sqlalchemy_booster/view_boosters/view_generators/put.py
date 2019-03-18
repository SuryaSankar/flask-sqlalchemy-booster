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
        fields_allowed_to_be_set=None,
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
            input_data = g.json
            if pre_processors is not None:
                for processor in pre_processors:
                    if callable(processor):
                        process_result = processor(data=input_data, existing_instance=obj)
                        if process_result and isinstance(process_result, Response):
                            return process_result

                        
            fields_to_be_removed = union([
                fields_forbidden_from_being_set or [],
                model_class._fields_forbidden_from_being_set_ or []])
            if len(fields_to_be_removed) > 0:
                delete_dict_keys(input_data, fields_to_be_removed)
            input_data = model_class.pre_validation_adapter(input_data, existing_instance=obj)
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