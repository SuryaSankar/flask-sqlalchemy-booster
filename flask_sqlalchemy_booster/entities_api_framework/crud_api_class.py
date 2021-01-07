from .crud_api_view import register_crud_routes_for_models
from . import entity_definition_keys as edk
from toolspy import transform_dict

class EntityOperation(object):
    def __init__(self, entity):
        self.entity = entity
        self.entity_group = entity.entity_group

    def to_dict(self):
        raise NotImplementedError

class Get(EntityOperation):

    method = 'get'

    def __init__(
            self, entity, url=None, enable_caching=False, cache_key_determiner=None,
            cache_timeout=None, view_function=None, query_modifier=None,
            permitted_object_getter=None, id_attr=None, response_dict_struct=None,
            response_dict_modifiers=None, exception_handler=None, access_checker=None):
        super(Get, self).__init__(entity)
        self.url = url
        self.enable_caching = enable_caching
        self.cache_key_determiner = cache_key_determiner
        self.cache_timeout = cache_timeout
        self.view_function = view_function
        self.query_modifier = query_modifier
        self.permitted_object_getter = permitted_object_getter
        self.id_attr = id_attr
        self.response_dict_struct = response_dict_struct
        self.response_dict_modifiers = response_dict_modifiers
        self.exception_handler = exception_handler
        self.access_checker = access_checker

    def to_dict(self):
        return transform_dict({
            edk.URL: self.url,
            edk.ENABLE_CACHING: self.enable_caching,
            edk.CACHE_KEY_DETERMINER: self.cache_key_determiner,
            edk.CACHE_TIMEOUT: self.cache_timeout,
            edk.VIEW_FUNC: self.view_function,
            edk.QUERY_MODIFIER: self.query_modifier,
            edk.PERMITTED_OPERATIONS: self.permitted_object_getter,
            edk.RESPONSE_DICT_STRUCT: self.response_dict_struct,
            edk.RESPONSE_DICT_MODIFIERS: self.response_dict_modifiers,
            edk.EXCEPTION_HANDLER: self.exception_handler,
            edk.ACCESS_CHECKER: self.access_checker,
        }, skip_none_vals=True)


class Index(EntityOperation):

    method = 'index'

    def __init__(
            self, entity, url=None, view_function=None, enable_caching=False,
            cache_key_determiner=None, cache_timeout=None, query_modifier=None,
            response_dict_struct=None, custom_response_creator=None,
            exception_handler=None, access_checker=None,
            default_limit=None, default_sort=None, default_orderby=None,
            default_offset=None, default_page=None, default_per_page=None):
        super(Index, self).__init__(entity)
        self.url = url
        self.view_function = view_function
        self.enable_caching = enable_caching
        self.cache_key_determiner = cache_key_determiner
        self.cache_timeout = cache_timeout
        self.query_modifier = query_modifier
        self.response_dict_struct = response_dict_struct
        self.custom_response_creator = custom_response_creator
        self.exception_handler = exception_handler
        self.access_checker = access_checker
        self.default_limit = default_limit
        self.default_sort = default_sort
        self.default_orderby = default_orderby
        self.default_offset = default_offset
        self.default_page = default_page
        self.default_per_page = default_per_page

    def to_dict(self):
        return transform_dict({
            edk.URL: self.url,
            edk.VIEW_FUNC: self.view_function,
            edk.ENABLE_CACHING: self.enable_caching,
            edk.CACHE_KEY_DETERMINER: self.cache_key_determiner,
            edk.CACHE_TIMEOUT: self.cache_timeout,
            edk.QUERY_MODIFIER: self.query_modifier,
            edk.RESPONSE_DICT_STRUCT: self.response_dict_struct,
            edk.CUSTOM_RESPONSE_CREATOR: self.custom_response_creator,
            edk.EXCEPTION_HANDLER: self.exception_handler,
            edk.ACCESS_CHECKER: self.access_checker,
            edk.DEFAULT_LIMIT: self.default_limit,
            edk.DEFAULT_SORT: self.default_sort,
            edk.DEFAULT_ORDERBY: self.default_orderby,
            edk.DEFAULT_OFFSET: self.default_offset,
            edk.DEFAULT_PAGE: self.default_page,
            edk.DEFAULT_PER_PAGE: self.default_per_page
        }, skip_none_vals=True)


class Post(EntityOperation):

    method = 'post'

    def __init__(
            self, entity, url=None, view_function=None, before_save=None, after_save=None,
            response_dict_struct=None, exception_handler=None, access_checker=None,
            settable_fields=None, non_settable_fields=None,
            remove_property_keys_before_validation=False, remove_relationship_keys_before_validation=False,
            remove_assoc_proxy_keys_before_validation=False, input_schema_modifier=None):
        super(Post, self).__init__(entity)
        self.url = url
        self.view_function = view_function
        self.before_save = before_save
        self.after_save = after_save
        self.response_dict_struct = response_dict_struct
        self.exception_handler = exception_handler
        self.access_checker = access_checker
        self.settable_fields = settable_fields
        self.non_settable_fields = non_settable_fields
        self.remove_property_keys_before_validation = remove_property_keys_before_validation
        self.remove_relationship_keys_before_validation = remove_relationship_keys_before_validation
        self.remove_assoc_proxy_keys_before_validation = remove_assoc_proxy_keys_before_validation
        self.input_schema_modifier = input_schema_modifier


    def to_dict(self):
        return transform_dict({
            edk.URL: self.url,
            edk.VIEW_FUNC: self.view_function,
            edk.BEFORE_SAVE_HANDLERS: self.before_save,
            edk.AFTER_SAVE_HANDLERS: self.after_save,
            edk.RESPONSE_DICT_STRUCT: self.response_dict_struct,
            edk.EXCEPTION_HANDLER: self.exception_handler,
            edk.ACCESS_CHECKER: self.access_checker,
            edk.SETTABLE_FIELDS: self.settable_fields,
            edk.NON_SETTABLE_FIELDS: self.non_settable_fields,
            edk.REMOVE_PROPERTY_KEYS_BEFORE_VALIDATION: self.remove_property_keys_before_validation,
            edk.REMOVE_RELATIONSHIP_KEYS_BEFORE_VALIDATION: self.remove_relationship_keys_before_validation,
            edk.REMOVE_ASSOC_PROXY_KEYS_BEFORE_VALIDATION: self.remove_assoc_proxy_keys_before_validation,
            edk.INPUT_SCHEMA_MODIFIER: self.input_schema_modifier
        }, skip_none_vals=True)

class Put(EntityOperation):

    method = 'put'

    def __init__(
            self, entity, url=None, view_function=None,query_modifier=None,
            permitted_object_getter=None,
            before_save=None, after_save=None,
            response_dict_struct=None, exception_handler=None, access_checker=None,
            settable_fields=None, non_settable_fields=None,
            remove_property_keys_before_validation=False, remove_relationship_keys_before_validation=False,
            remove_assoc_proxy_keys_before_validation=False, input_schema_modifier=None):
        super(Put, self).__init__(entity)
        self.url = url
        self.view_function = view_function
        self.query_modifier = query_modifier
        self.permitted_object_getter = permitted_object_getter
        self.before_save = before_save
        self.after_save = after_save
        self.response_dict_struct = response_dict_struct
        self.exception_handler = exception_handler
        self.access_checker = access_checker
        self.settable_fields = settable_fields
        self.non_settable_fields = non_settable_fields
        self.remove_property_keys_before_validation = remove_property_keys_before_validation
        self.remove_relationship_keys_before_validation = remove_relationship_keys_before_validation
        self.remove_assoc_proxy_keys_before_validation = remove_assoc_proxy_keys_before_validation
        self.input_schema_modifier = input_schema_modifier


    def to_dict(self):
        return transform_dict({
            edk.URL: self.url,
            edk.VIEW_FUNC: self.view_function,
            edk.QUERY_MODIFIER: self.query_modifier,
            edk.PERMITTED_OBJECT_GETTER: self.permitted_object_getter,
            edk.BEFORE_SAVE_HANDLERS: self.before_save,
            edk.AFTER_SAVE_HANDLERS: self.after_save,
            edk.RESPONSE_DICT_STRUCT: self.response_dict_struct,
            edk.EXCEPTION_HANDLER: self.exception_handler,
            edk.ACCESS_CHECKER: self.access_checker,
            edk.SETTABLE_FIELDS: self.settable_fields,
            edk.NON_SETTABLE_FIELDS: self.non_settable_fields,
            edk.REMOVE_PROPERTY_KEYS_BEFORE_VALIDATION: self.remove_property_keys_before_validation,
            edk.REMOVE_RELATIONSHIP_KEYS_BEFORE_VALIDATION: self.remove_relationship_keys_before_validation,
            edk.REMOVE_ASSOC_PROXY_KEYS_BEFORE_VALIDATION: self.remove_assoc_proxy_keys_before_validation,
            edk.INPUT_SCHEMA_MODIFIER: self.input_schema_modifier
        }, skip_none_vals=True)


class Patch(EntityOperation):

    method = 'patch'

    def __init__(
            self, entity, url=None, view_function=None, query_modifier=None,
            command_processors=None, before_save=None, after_save=None,
            response_dict_struct=None, exception_handler=None, access_checker=None,
            settable_fields=None, non_settable_fields=None,
            remove_property_keys_before_validation=False, remove_relationship_keys_before_validation=False,
            remove_assoc_proxy_keys_before_validation=False, input_schema_modifier=None):
        super(Patch, self).__init__(entity)
        self.url = url
        self.view_function = view_function
        self.query_modifier = query_modifier
        self.command_processors = command_processors
        self.before_save = before_save
        self.after_save = after_save
        self.response_dict_struct = response_dict_struct
        self.exception_handler = exception_handler
        self.access_checker = access_checker
        self.settable_fields = settable_fields
        self.non_settable_fields = non_settable_fields
        self.remove_property_keys_before_validation = remove_property_keys_before_validation
        self.remove_relationship_keys_before_validation = remove_relationship_keys_before_validation
        self.remove_assoc_proxy_keys_before_validation = remove_assoc_proxy_keys_before_validation
        self.input_schema_modifier = input_schema_modifier


    def to_dict(self):
        return transform_dict({
            edk.URL: self.url,
            edk.VIEW_FUNC: self.view_function,
            edk.QUERY_MODIFIER: self.query_modifier,
            edk.BEFORE_SAVE_HANDLERS: self.before_save,
            edk.AFTER_SAVE_HANDLERS: self.after_save,
            edk.RESPONSE_DICT_STRUCT: self.response_dict_struct,
            edk.EXCEPTION_HANDLER: self.exception_handler,
            edk.ACCESS_CHECKER: self.access_checker,
            edk.SETTABLE_FIELDS: self.settable_fields,
            edk.NON_SETTABLE_FIELDS: self.non_settable_fields,
            edk.REMOVE_PROPERTY_KEYS_BEFORE_VALIDATION: self.remove_property_keys_before_validation,
            edk.REMOVE_RELATIONSHIP_KEYS_BEFORE_VALIDATION: self.remove_relationship_keys_before_validation,
            edk.REMOVE_ASSOC_PROXY_KEYS_BEFORE_VALIDATION: self.remove_assoc_proxy_keys_before_validation,
            edk.INPUT_SCHEMA_MODIFIER: self.input_schema_modifier
        }, skip_none_vals=True)

class Delete(EntityOperation):

    method = 'delete'

    def __init__(
            self, entity, url=None, view_function=None, query_modifier=None,
            permitted_object_getter=None,
            before_save=None, after_save=None,
            response_dict_struct=None, exception_handler=None, access_checker=None,
            settable_fields=None, non_settable_fields=None,
            remove_property_keys_before_validation=False, remove_relationship_keys_before_validation=False,
            remove_assoc_proxy_keys_before_validation=False, input_schema_modifier=None):
        super(Delete, self).__init__(entity)
        self.url = url
        self.view_function = view_function
        self.query_modifier = query_modifier
        self.permitted_object_getter = permitted_object_getter
        self.before_save = before_save
        self.after_save = after_save
        self.response_dict_struct = response_dict_struct
        self.exception_handler = exception_handler
        self.access_checker = access_checker
        self.settable_fields = settable_fields
        self.non_settable_fields = non_settable_fields
        self.remove_property_keys_before_validation = remove_property_keys_before_validation
        self.remove_relationship_keys_before_validation = remove_relationship_keys_before_validation
        self.remove_assoc_proxy_keys_before_validation = remove_assoc_proxy_keys_before_validation
        self.input_schema_modifier = input_schema_modifier


    def to_dict(self):
        return transform_dict({
            edk.URL: self.url,
            edk.VIEW_FUNC: self.view_function,
            edk.QUERY_MODIFIER: self.query_modifier,
            edk.PERMITTED_OBJECT_GETTER: self.permitted_object_getter,
            edk.BEFORE_SAVE_HANDLERS: self.before_save,
            edk.AFTER_SAVE_HANDLERS: self.after_save,
            edk.RESPONSE_DICT_STRUCT: self.response_dict_struct,
            edk.EXCEPTION_HANDLER: self.exception_handler,
            edk.ACCESS_CHECKER: self.access_checker,
            edk.SETTABLE_FIELDS: self.settable_fields,
            edk.NON_SETTABLE_FIELDS: self.non_settable_fields,
            edk.REMOVE_PROPERTY_KEYS_BEFORE_VALIDATION: self.remove_property_keys_before_validation,
            edk.REMOVE_RELATIONSHIP_KEYS_BEFORE_VALIDATION: self.remove_relationship_keys_before_validation,
            edk.REMOVE_ASSOC_PROXY_KEYS_BEFORE_VALIDATION: self.remove_assoc_proxy_keys_before_validation,
            edk.INPUT_SCHEMA_MODIFIER: self.input_schema_modifier
        }, skip_none_vals=True)

class BatchSave(EntityOperation):

    method = 'batch_save'

    def __init__(self, entity):
        super(BatchSave, self).__init__(entity)


class Entity(object):
    def __init__(
            self, url_slug=None, model_class=None, entity_set=None, permitted_operations=None, 
            forbidden_operations=None, endpoint_slug=None,
            query_modifier=None, access_checker=None, exception_handler=None, response_dict_modifiers=None,
            id_attr=None, response_dict_struct=None, non_settable_fields=None, settable_fields=None,
            remove_relationship_keys_before_validation=False, remove_assoc_proxy_keys_before_validation=False,
            remove_property_keys_before_validation=False, enable_caching=False, cache_timeout=None):
        self.model_class = model_class
        self.entity_set = entity_set
        self.url_slug = url_slug
        self.permitted_operations = permitted_operations
        self.forbidden_operations = forbidden_operations
        self.endpoint_slug = endpoint_slug
        self.query_modifier = query_modifier
        self.access_checker = access_checker
        self.exception_handler = exception_handler
        self.response_dict_modifiers = response_dict_modifiers
        self.response_dict_struct = response_dict_struct
        self.id_attr = id_attr
        self.non_settable_fields = non_settable_fields
        self.settable_fields = settable_fields
        self.enable_caching = enable_caching
        self.cache_timeout = cache_timeout
        self.remove_relationship_keys_before_validation = remove_relationship_keys_before_validation
        self.remove_assoc_proxy_keys_before_validation = remove_assoc_proxy_keys_before_validation
        self.remove_property_keys_before_validation = remove_property_keys_before_validation



    def to_dict(self):
        return transform_dict({
            edk.URL_SLUG: self.url_slug,
            edk.PERMITTED_OPERATIONS: self.permitted_operations,
            edk.FORBIDDEN_OPERATIONS: self.forbidden_operations,
            edk.ENDPOINT_SLUG: self.endpoint_slug,
            edk.QUERY_MODIFIER: self.query_modifier,
            edk.ACCESS_CHECKER: self.access_checker,
            edk.EXCEPTION_HANDLER: self.exception_handler,
            edk.RESPONSE_DICT_MODIFIERS: self.response_dict_modifiers,
            edk.RESPONSE_DICT_STRUCT: self.response_dict_struct,
            edk.ID_ATTR: self.id_attr,
            edk.NON_SETTABLE_FIELDS: self.non_settable_fields,
            edk.SETTABLE_FIELDS: self.settable_fields,
            edk.ENABLE_CACHING: self.enable_caching,
            edk.CACHE_TIMEOUT: self.cache_timeout,
            edk.REMOVE_RELATIONSHIP_KEYS_BEFORE_VALIDATION: self.remove_relationship_keys_before_validation,
            edk.REMOVE_ASSOC_PROXY_KEYS_BEFORE_VALIDATION: self.remove_assoc_proxy_keys_before_validation,
            edk.REMOVE_PROPERTY_KEYS_BEFORE_VALIDATION: self.remove_property_keys_before_validation
        }, skip_none_vals=True)



class EntitiesGroup(object):
    all_operations = ['index', 'get', 'post', 'put', 'patch', 'delete', 'batch_save']

    def __init__(self,
        app_or_bp=None, allow_unknown_fields=False, 
        cache_handler=None, exception_handler=None,
        tmp_folder_path="/tmp", permitted_operations=None,
        forbidden_operations=None, celery_worker=None,
        register_schema_definition=False, register_views_map=False,
        schema_def_url='/schema-def', views_map_url='/views-map',
        entities=None, register_routes=True
    ):
        self.schema_definition = {
            "models_registered_for_views": [],
            "model_schemas": {

            },
            "views": {

            }
        }
        self.entities = entities
        self.allow_unknown_fields = allow_unknown_fields
        self.cache_handler = cache_handler
        self.exception_handler = exception_handler
        self.tmp_folder_path = tmp_folder_path
        self.permitted_operations = permitted_operations
        self.forbidden_operations = forbidden_operations
        self.celery_worker = celery_worker
        self.register_schema_definition = register_schema_definition
        self.register_views_map = register_views_map
        self.schema_def_url = schema_def_url
        self.views_map_url = views_map_url
        if app_or_bp:
            self.initialize(app_or_bp, register_routes=register_routes)

    def initialize(self, app_or_bp, register_routes=True):
        self.app_or_bp = app_or_bp
        if register_routes:
            self.register_routes(self.app_or_bp)

    def register_routes(self, app_or_bp=None):
        register_crud_routes_for_models(
            app_or_bp or self.app_or_bp, self.to_dict(),
            allow_unknown_fields=self.allow_unknown_fields, cache_handler=self.cache_handler, 
            exception_handler=self.exception_handler, tmp_folder_path=self.tmp_folder_path,
            permitted_operations=self.permitted_operations, forbidden_operations=self.forbidden_operations, 
            celery_worker=self.celery_worker, register_schema_definition=self.register_schema_definition,
            register_views_map=self.register_views_map,
            schema_def_url=self.schema_def_url, views_map_url=self.views_map_url
        )


    def to_dict(self):
        entities_map = {}
        for entity in self.entities:
            entities_map[entity.model_class or entity.model_name] = entity.to_dict()
        return entities_map

