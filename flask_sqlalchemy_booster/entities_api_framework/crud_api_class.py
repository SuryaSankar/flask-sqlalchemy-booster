from flask import Response
import json
from schemalite.core import json_encoder


from .crud_api_view import (
    register_crud_routes_for_models, construct_get_view_function,
    construct_index_view_function, construct_post_view_function,
    construct_put_view_function, construct_delete_view_function,
    construct_patch_view_function, construct_batch_save_view_function)
from . import entity_definition_keys as edk
from toolspy import (
    all_subclasses, fetch_nested_key_from_dict, fetch_nested_key,
    delete_dict_keys, union, merge, difference, transform_dict)
from copy import deepcopy


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
            self, entity, url=None, view_function=None, enable_caching=None,
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
            self, url_slug=None, model_class=None, name=None, entities_group=None, permitted_operations=None, 
            forbidden_operations=None, endpoint_slug=None,
            query_modifier=None, access_checker=None, exception_handler=None, response_dict_modifiers=None,
            id_attr=None, response_dict_struct=None, non_settable_fields=None, settable_fields=None,
            remove_relationship_keys_before_validation=False, remove_assoc_proxy_keys_before_validation=False,
            remove_property_keys_before_validation=False, enable_caching=False, cache_timeout=None):
        self.model_class = model_class
        self.name = name or self.model_class.__name__
        self.entities_group = entities_group
        if self.entities_group:
            if self not in self.entities_group.entities:
                self.entities_group.entities.append(self)
                self.entities_map[self.name] = self
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
        self.non_settable_fields = non_settable_fields if non_settable_fields else []
        self.settable_fields = settable_fields if settable_fields else []
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
        self.entities_map = {}
        for entity in self.entities:
            entity.entity_group = self
            self.entities_map[entity.name] = entity
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
        self.registry = {}
        if app_or_bp:
            self.initialize(app_or_bp, register_routes=register_routes)

    def add_entity(self, entity):
        if entity not in self.entities:
            self.entities.append(entity)
        entity.entity_group = self
        self.entities_map[entity.name] = entity

    def get_entity(self, entity_name):
        return self.entities_map.get(entity_name)

    def get_registry_entry(self, app_or_bp, url_prefix):
        return self.registry.get((app_or_bp, url_prefix))

    def initialize_registry_entry(self, app_or_bp, url_prefix):
            self.registry[(app_or_bp, url_prefix)] = {
                "models_registered_for_views": [],
                "model_schemas": {

                },
                edk.OPERATION_MODIFIERS: {

                }
            }
    def initialize(self, app_or_bp, register_routes=True):
        self.app_or_bp = app_or_bp
        if register_routes:
            # self.register_routes(self.app_or_bp)
            self.register_crud_routes(self.app_or_bp)

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


    def register_crud_routes(
            self, app_or_bp, url_prefix=None,
            allow_unknown_fields=False, cache_handler=None, exception_handler=None,
            tmp_folder_path="/tmp", permitted_operations=None,
            forbidden_operations=None, celery_worker=None,
            register_schema_definition=False, register_views_map=False,
            schema_def_url='/schema-def', views_map_url='/views-map'):

        all_operations = [Index, Get, Post, Put, Patch, Delete, BatchSave]

        if self.get_registry_entry(app_or_bp, url_prefix) is None:
            self.initialize_registry_entry(app_or_bp, url_prefix)
        registry = self.get_registry_entry(app_or_bp, url_prefix)

        model_schemas = registry["model_schemas"]

        def populate_model_schema(entity):
            if entity.model_class._input_data_schema_:
                input_schema = deepcopy(entity.model_class._input_data_schema_)
            else:
                input_schema = entity.model_class.generate_input_data_schema()
            if callable(entity.model_class.input_schema_modifier):
                input_schema = entity.model_class.input_schema_modifier(
                    input_schema)
            model_schemas[entity.name] = {
                "input_schema": input_schema,
                "output_schema": entity.model_class.output_data_schema(),
                "accepted_data_structure": entity.model_class.max_permissible_dict_structure()
            }
            for subcls in all_subclasses(entity.model_class):
                if subcls.__name__ not in model_schemas:
                    model_schemas[subcls.__name__] = {
                        'is_a_polymorphically_derived_from': entity.model_class.__name__,
                        'polymorphic_identity': subcls.__mapper_args__['polymorphic_identity']
                    }
            for rel in entity.model_class.__mapper__.relationships.values():
                if rel.mapper.class_.__name__ not in model_schemas:
                    populate_model_schema(rel.mapper.class_)

        for entity in self.entities:
            _model = entity.model_class
            _model_name = entity.name
            base_url = entity.url_slug
            # base_url = _model_dict.get(edk.URL_SLUG)

            if entity.permitted_operations:
                permitted_actions = entity.permitted_operations
            elif entity.forbidden_operations:
                permitted_actions = difference(
                    all_operations, entity.forbidden_operations)
            elif permitted_operations is not None:
                permitted_actions = permitted_operations
            elif forbidden_operations is not None:
                permitted_actions = difference(
                    all_operations, forbidden_operations)
            else:
                permitted_actions = all_operations

            default_query_constructor = entity.query_modifier
            default_access_checker = entity.access_checker
            default_exception_handler = entity.exception_handler or exception_handler
            default_dict_post_processors = entity.response_dict_modifiers
            default_id_attr = entity.id_attr
            dict_struct_for_model = entity.response_dict_struct
            fields_forbidden_from_being_set_for_all_views = entity.non_settable_fields or []
            fields_allowed_to_be_set_for_all_views = entity.settable_fields or []
            remove_relationship_keys_before_validation = entity.remove_relationship_keys_before_validation
            remove_assoc_proxy_keys_before_validation = entity.remove_assoc_proxy_keys_before_validation
            remove_property_keys_before_validation = entity.remove_property_keys_before_validation
            enable_caching = entity.enable_caching and cache_handler is not None
            cache_timeout = entity.cache_timeout
            endpoint_slug = entity.endpoint_slug or _model.__tablename__

            if _model_name not in registry["models_registered_for_views"]:
                registry["models_registered_for_views"].append(
                    _model_name)
            if _model_name not in model_schemas:
                populate_model_schema(entity)

            if _model._input_data_schema_:
                model_default_input_schema = deepcopy(_model._input_data_schema_)
            else:
                model_default_input_schema = _model.generate_input_data_schema()
            if callable(entity.input_schema_modifier):
                model_default_input_schema = entity.input_schema_modifier(
                    model_default_input_schema)

            views = registry[edk.OPERATION_MODIFIERS]
            schemas_registry = {k: v.get('input_schema')
                                for k, v in list(model_schemas.items())}
            if _model_name not in views:
                views[_model_name] = {}

            if Index in permitted_actions:
                index_op = entity.index or Index(entity=entity)
                if index_op.enable_caching is not None:
                    enable_caching = index_op.enable_caching and cache_handler is not None
                cache_key_determiner = index_op.cache_key_determiner
                cache_timeout = index_op.cache_timeout or cache_timeout
                index_func = index_op.view_func or construct_index_view_function(
                    _model,
                    index_query_creator=index_op.query_modifier or default_query_constructor,
                    dict_struct=index_op.response_dict_struct or dict_struct_for_model,
                    custom_response_creator=index_op.custom_response_creator,
                    enable_caching=enable_caching,
                    cache_handler=cache_handler,
                    cache_key_determiner=cache_key_determiner,
                    cache_timeout=cache_timeout,
                    exception_handler=index_op.exception_handler or default_exception_handler,
                    access_checker=index_op.access_checker or default_access_checker,
                    default_limit=index_op.default_limit,
                    default_sort=index_op.default_sort,
                    default_orderby=index_op.default_orderby,
                    default_offset=index_op.default_offset,
                    default_page=index_op.default_page,
                    default_per_page=index_op.default_per_page
                )
                index_url = index_op.url or "/%s" % base_url
                app_or_bp.route(
                    index_url, methods=['GET'], endpoint='index_%s' % endpoint_slug)(
                    index_func)
                views[_model_name][edk.INDEX] = {edk.URL: index_url}

            if Get in permitted_actions:
                get_op = entity.get or Get(entity=entity)
                if get_op.enable_caching is not None:
                    enable_caching = get_op.enable_caching and cache_handler is not None
                cache_key_determiner = get_op.cache_handler
                cache_timeout = get_op.cache_timeout or cache_timeout
                get_func = get_op.view_func or construct_get_view_function(
                    _model,
                    permitted_object_getter=get_op.permitted_object_getter or entity.permitted_object_getter,
                    get_query_creator=get_op.query_modifier or default_query_constructor,
                    dict_struct=get_op.response_dict_struct or dict_struct_for_model,
                    enable_caching=enable_caching,
                    cache_handler=cache_handler, cache_key_determiner=cache_key_determiner,
                    cache_timeout=cache_timeout,
                    exception_handler=get_op.exception_handler or default_exception_handler,
                    access_checker=get_op.access_checker or default_access_checker,
                    id_attr_name=get_op.id_attr or default_id_attr,
                    dict_post_processors=get_op.response_dict_modifiers or default_dict_post_processors)
                get_url = get_op.url or '/%s/<_id>' % base_url
                app_or_bp.route(
                    get_url, methods=['GET'], endpoint='get_%s' % endpoint_slug)(
                    get_func)
                views[_model_name]['get'] = {edk.URL: get_url}

            if Post in permitted_actions:
                post_op = entity.post or Post(entity=entity)
                if callable(post_op.input_schema_modifier):
                    post_input_schema = post_op.input_schema_modifier(
                        deepcopy(model_default_input_schema))
                else:
                    post_input_schema = model_default_input_schema
                post_func = post_op.view_func or construct_post_view_function(
                    _model, post_input_schema,
                    entities_group=self,
                    pre_processors=post_op.actions_before_save,
                    post_processors=post_op.actions_after_save,
                    schemas_registry=schemas_registry,
                    allow_unknown_fields=allow_unknown_fields,
                    dict_struct=post_op.response_dict_struct or dict_struct_for_model,
                    exception_handler=post_op.exception_handler or default_exception_handler,
                    access_checker=post_op.access_checker or default_access_checker,
                    remove_property_keys_before_validation=post_op.remove_property_keys_before_validation 
                    if post_op.remove_property_keys_before_validation is not None
                    else remove_property_keys_before_validation,
                    remove_relationship_keys_before_validation=post_op.remove_relationship_keys_before_validation 
                    if post_op.remove_relationship_keys_before_validation is not None 
                    else remove_relationship_keys_before_validation,
                    remove_assoc_proxy_keys_before_validation=post_op.remove_assoc_proxy_keys_before_validation
                    if post_op.remove_assoc_proxy_keys_before_validation is not None 
                    else remove_assoc_proxy_keys_before_validation,
                    fields_allowed_to_be_set=post_op.settable_fields or fields_allowed_to_be_set_for_all_views,
                    fields_forbidden_from_being_set=union([
                        fields_forbidden_from_being_set_for_all_views,
                        post_op.non_settable_fields or []
                    ]))
                post_url = post_op.url or "/%s" % base_url
                app_or_bp.route(
                    post_url, methods=['POST'], endpoint='post_%s' % endpoint_slug)(
                    post_func)
                views[_model_name]['post'] = {edk.URL: post_url}
                if callable(post_op.input_schema_modifier):
                    views[_model_name]['post']['input_schema'] = post_op.input_schema_modifier(
                        deepcopy(model_schemas[_model.__name__]['input_schema']))

            if Put in permitted_actions:
                put_op = entity.put or Put(entity=entity)
                if callable(put_op.input_schema_modifier):
                    put_input_schema = put_op.input_schema_modifier(
                        deepcopy(model_default_input_schema))
                else:
                    put_input_schema = model_default_input_schema
                put_func = put_op.view_func or construct_put_view_function(
                    _model, put_input_schema,
                    entities_group=self,
                    permitted_object_getter=put_op.permitted_object_getter or entity.permitted_object_getter,
                    pre_processors=put_op.actions_before_save,
                    post_processors=post_op.actions_after_save,
                    dict_struct=put_op.response_dict_struct or dict_struct_for_model,
                    allow_unknown_fields=allow_unknown_fields,
                    query_constructor=put_op.query_modifier or default_query_constructor,
                    schemas_registry=schemas_registry,
                    exception_handler=put_op.exception_handler or default_exception_handler,
                    access_checker=put_op.access_checker or default_access_checker,
                    remove_property_keys_before_validation=put_op.remove_property_keys_before_validation 
                    if put_op.remove_property_keys_before_validation is not None 
                    else remove_property_keys_before_validation,
                    remove_relationship_keys_before_validation=put_op.remove_relationship_keys_before_validation
                    if put_op.remove_relationship_keys_before_validation is not None
                    else remove_relationship_keys_before_validation,
                    remove_assoc_proxy_keys_before_validation=put_op.remove_assoc_proxy_keys_before_validation
                    if put_op.remove_assoc_proxy_keys_before_validation is not None
                    else remove_assoc_proxy_keys_before_validation,
                    fields_allowed_to_be_set=put_op.settable_fields or fields_allowed_to_be_set_for_all_views,
                    fields_forbidden_from_being_set=union([
                        fields_forbidden_from_being_set_for_all_views,
                        put_op.non_settable_fields or []
                    ]))
                put_url = put_op.url or "/%s/<_id>" % base_url
                app_or_bp.route(
                    put_url, methods=['PUT'], endpoint='put_%s' % endpoint_slug)(
                    put_func)
                views[_model_name]['put'] = {edk.URL: put_url}
                if callable(put_op.input_schema_modifier):
                    views[_model_name]['put']['input_schema'] = put_op.input_schema_modifier(
                        deepcopy(model_schemas[_model.__name__]['input_schema']))

            if Patch in permitted_actions:
                patch_op = entity.patch or Patch(entity=entity)
                if callable(patch_op.input_schema_modifier):
                    patch_input_schema = patch_op.input_schema_modifier(
                        deepcopy(model_default_input_schema))
                else:
                    patch_input_schema = model_default_input_schema
                patch_func = patch_op.view_func or construct_patch_view_function(
                    _model, patch_input_schema,
                    pre_processors=patch_op.actions_before_save,
                    processors=patch_op.processors,
                    post_processors=patch_op.actions_after_save,
                    query_constructor=patch_op.query_modifier or default_query_constructor,
                    permitted_object_getter=patch_op.permitted_object_getter or entity.permitted_object_getter,
                    schemas_registry=schemas_registry,
                    exception_handler=patch_op.exception_handler or default_exception_handler,
                    access_checker=patch_op.access_checker or default_access_checker,
                    dict_struct=patch_op.response_dict_struct or dict_struct_for_model)
                patch_url = patch_op.url or "/%s/<_id>" % base_url
                app_or_bp.route(
                    patch_url, methods=['PATCH'], endpoint='patch_%s' % endpoint_slug)(
                    patch_func)
                views[_model_name]['patch'] = {edk.URL: patch_url}
                if callable(patch_op.input_schema_modifier):
                    views[_model_name]['patch']['input_schema'] = patch_op.input_schema_modifier(
                        deepcopy(model_schemas[_model.__name__]['input_schema']))

            if Delete in permitted_actions:
                delete_op = entity.delete or Delete(entity=entity)
                delete_func = delete_op.view_func or construct_delete_view_function(
                    _model,
                    query_constructor=delete_op.query_modifier or default_query_constructor,
                    pre_processors=delete_op.actions_before_save,
                    permitted_object_getter=delete_op.permitted_object_getter or entity.permitted_object_getter,
                    post_processors=delete_op.actions_after_save,
                    exception_handler=delete_op.exception_handler or default_exception_handler,
                    access_checker=delete_op.access_checker or default_access_checker)
                delete_url = delete_op.url or "/%s/<_id>" % base_url
                app_or_bp.route(
                    delete_url, methods=['DELETE'], endpoint='delete_%s' % endpoint_slug)(
                    delete_func)
                views[_model_name]['delete'] = {edk.URL: delete_url}

            if BatchSave in permitted_actions:
                batch_save_op = entity.batch_save or BatchSave(entity=entity)
                if callable(batch_save_op.input_schema_modifier):
                    batch_save_input_schema = batch_save_op.input_schema_modifier(
                        deepcopy(model_default_input_schema))
                else:
                    batch_save_input_schema = model_default_input_schema
                batch_save_func = batch_save_op.view_func or construct_batch_save_view_function(
                    _model, batch_save_input_schema,
                    app_or_bp=app_or_bp,
                    pre_processors_for_post=fetch_nested_key(entity, 'post.actions_before_save'),
                    pre_processors_for_put=fetch_nested_key(entity, 'put.actions_before_save'),
                    post_processors_for_post=fetch_nested_key(entity, 'post.actions_after_save'),
                    post_processors_for_put=fetch_nested_key(entity, 'put.actions_before_save'),
                    extra_pre_processors=batch_save_op.extra_actions_before_save,
                    extra_post_processors=batch_save_op.extra_actions_after_save,
                    unique_identifier_fields=batch_save_op.unique_identifier_fields,
                    dict_struct=batch_save_op.response_dict_struct or dict_struct_for_model,
                    allow_unknown_fields=allow_unknown_fields,
                    query_constructor=batch_save_op.query_modifier or default_query_constructor,
                    schemas_registry=schemas_registry,
                    exception_handler=batch_save_op.exception_handler or default_exception_handler,
                    tmp_folder_path=tmp_folder_path,
                    fields_forbidden_from_being_set=union([
                        fields_forbidden_from_being_set_for_all_views,
                        batch_save_op.non_settable_fields or []
                    ]),
                    celery_worker=celery_worker,
                    result_saving_instance_model=batch_save_op.result_saving_instance_model,
                    result_saving_instance_getter=batch_save_op.result_saving_instance_getter,
                    run_as_async_task=batch_save_op.run_as_async_task
                )
                batch_save_url = batch_save_op.url or "/batch-save/%s" % base_url
                app_or_bp.route(
                    batch_save_url, methods=['POST'], endpoint='batch_save_%s' % endpoint_slug)(
                    batch_save_func)
                views[_model_name]['batch_save'] = {edk.URL: batch_save_url}
                if callable(batch_save_op.input_schema_modifier):
                    views[_model_name]['batch_save']['input_schema'] = batch_save_op.input_schema_modifier(
                        deepcopy(model_schemas[_model.__name__]['input_schema']))

        if register_schema_definition:
            def schema_def():
                return Response(
                    json.dumps(
                        registry,
                        default=json_encoder, sort_keys=True),
                    200, mimetype='application/json')
            if cache_handler:
                schema_def = cache_handler.cached(timeout=86400)(schema_def)
            app_or_bp.route(schema_def_url, methods=['GET'])(schema_def)

        if register_views_map:
            def views_map():
                return Response(
                    json.dumps(
                        registry[edk.OPERATION_MODIFIERS],
                        default=json_encoder, sort_keys=True),
                    200, mimetype='application/json')
            if cache_handler:
                views_map = cache_handler.cached(timeout=86400)(views_map)
            app_or_bp.route(views_map_url, methods=['GET'])(views_map)


