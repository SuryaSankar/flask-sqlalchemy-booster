

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
            if '_ret' in g.args:
                rels = g.args['_ret'].split(".")
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
