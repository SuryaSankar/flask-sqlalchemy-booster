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