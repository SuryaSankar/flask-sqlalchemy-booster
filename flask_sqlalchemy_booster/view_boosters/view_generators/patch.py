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