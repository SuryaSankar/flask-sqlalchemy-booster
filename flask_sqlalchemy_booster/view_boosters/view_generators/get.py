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
                return key
            cache_key_determiner = make_key_prefix
        cached_get = cache_handler.memoize(
            timeout=cache_timeout,
            make_name=cache_key_determiner)(get)
        return cached_get
    return get