from flask import Response
import json
from schemalite.core import json_encoder

from .crud_constructors import (
    construct_get_view_function,
    construct_index_view_function, construct_post_view_function,
    construct_put_view_function, construct_delete_view_function,
    construct_patch_view_function, construct_batch_save_view_function)
from . import entity_definition_keys as edk
from toolspy import (
    all_subclasses, fetch_nested_key_from_dict, fetch_nested_key,
    delete_dict_keys, union, merge, difference, transform_dict)
from copy import deepcopy


class EntityOperation(object):
    """
    Base class which represents a crud operation on the entity
    """
    def __init__(self, entity=None):
        self.init_entity(entity)

    def init_entity(self, entity=None):
        self.entity = entity

    def to_dict(self):
        raise NotImplementedError



class Get(EntityOperation):
    """This class represents a GET operation on an entity.
    Registers a GET endpoint at /<entity.url_slug>/<id>

    Parameters
    ------------
    entity: Entity
        The entity object on which the Get operation is defined. Should be specified if the get
        operation is defined separately after the entity is defined. Can be skipped if it is instead
        defined as a part of the entity definition

    query_modifier: function, Optional
        A function which can modify the query used to fetch the object to be returned. By default
        the router obtains the instance to be fetched by Get by filtering the id attribute
        to be equal to the value of the id in the url.
        If we want to set some more filters before filtering
        should be a function which accepts a query and returns a query
        For example, if an api is supposed to return only confirmed orders, we can set the
        query_modifier like this
            
            query_modifier = lambda q: q.filter(Order.confirmed==True)

        This will take precedence over the query_modifier defined at entity level

    permitted_object_getter: function, optional
        A function which if set, will be used to retrieve the object to get. If This
        callable is set, then this will be used instead of the query used to get
        the object by default.
        For example if you want to get the current user always when registering user
        model in an api, you can set like this

            >>> Get(permitted_object_getter=lambda: current_user)

        This will take precedence over the permitted_object_getter defined at entity level

    id_attr: str, optional
        By default the primary key is used as the id attribute. But we can modify it to some
        other field. For example if we want the url to be like /users/abcd@xyz.com, then we cant
        set

            >>> Get(id_attr='email')

    response_dict_struct: dict, optional
        The dictionary used to specify the structure of the object

        Example:

            Get(
                response_dict_struct=dict(
                    attrs=["id", "name", "description"],
                    rels={
                        "tasks": dict(
                            attrs=["id", "title"],
                            rels={
                                "assignees": dict(attrs=["name", "email"])
                            }
                        ),
                        "projects": {}
                    }
            )

    response_dict_modifiers: List[Callable[[dict, model instance], dict]], Optional
        A list of functions, where each function should be able to accept the response
        dictionary as the first argument and the instance which is being fetched 
        as the second argument, and then make any modifications as required to the
        response dict and return it

        
    url: str
        Optional. Provide this if you want to override the default url for the Get
        operation which is of the format /<entity.url_slug>/<id>. For example if you
        want to define a special endpoint /accounts/current which will let the client
        access the currently logged in account without knowing the id, then you would need
        to set this url parameter

    
    """


    method = 'get'

    def __init__(
            self, entity=None, view_function=None, query_modifier=None,
            permitted_object_getter=None, id_attr=None, response_dict_struct=None,
            response_dict_modifiers=None, exception_handler=None, access_checker=None,
            url=None, enable_caching=False, cache_key_determiner=None,
            cache_timeout=None, ):
        super(Get, self).__init__(entity=entity)
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
            self, entity=None, url=None, view_function=None, enable_caching=None,
            cache_key_determiner=None, cache_timeout=None, query_modifier=None,
            response_dict_struct=None, custom_response_creator=None,
            exception_handler=None, access_checker=None,
            default_limit=None, default_sort=None, default_orderby=None,
            default_offset=None, default_page=None, default_per_page=None):
        super(Index, self).__init__(entity=entity)
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
            self, entity=None, url=None, view_function=None, before_save=None, after_save=None,
            response_dict_struct=None, exception_handler=None, access_checker=None,
            settable_fields=None, non_settable_fields=None,
            remove_property_keys_before_validation=False, remove_relationship_keys_before_validation=False,
            remove_assoc_proxy_keys_before_validation=False, input_schema_modifier=None):
        super(Post, self).__init__(entity=entity)
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
            self, entity=None, url=None, view_function=None,
            query_modifier=None,
            permitted_object_getter=None,
            before_save=None, after_save=None,
            response_dict_struct=None, exception_handler=None, access_checker=None,
            settable_fields=None, non_settable_fields=None,
            remove_property_keys_before_validation=False, remove_relationship_keys_before_validation=False,
            remove_assoc_proxy_keys_before_validation=False, input_schema_modifier=None):
        super(Put, self).__init__(entity=entity)
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
            self, entity=None, url=None, view_function=None, query_modifier=None,
            commands=None, permitted_object_getter=None,
            before_save=None, after_save=None,
            response_dict_struct=None, exception_handler=None, access_checker=None,
            settable_fields=None, non_settable_fields=None,
            remove_property_keys_before_validation=False, remove_relationship_keys_before_validation=False,
            remove_assoc_proxy_keys_before_validation=False, input_schema_modifier=None):
        super(Patch, self).__init__(entity=entity)
        self.url = url
        self.view_function = view_function
        self.query_modifier = query_modifier
        self.permitted_object_getter = permitted_object_getter
        self.commands = commands
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
            self, entity=None, url=None, view_function=None, query_modifier=None,
            permitted_object_getter=None,
            before_save=None, after_save=None,
            response_dict_struct=None, exception_handler=None, access_checker=None,
            settable_fields=None, non_settable_fields=None,
            remove_property_keys_before_validation=False, remove_relationship_keys_before_validation=False,
            remove_assoc_proxy_keys_before_validation=False, input_schema_modifier=None):
        super(Delete, self).__init__(entity=entity)
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

    def __init__(
            self, entity=None, url=None, view_function=None, query_modifier=None,
            permitted_object_getter=None, unique_identifier_fields=None, 
            before_save=None, after_save=None,
            extra_actions_before_save=None, extra_actions_after_save=None,
            result_saving_instance_model=None,
            result_saving_instance_getter=None,
            run_as_async_task=False, celery_worker=None,
            response_dict_struct=None, exception_handler=None, access_checker=None,
            settable_fields=None, non_settable_fields=None,
            remove_property_keys_before_validation=False, remove_relationship_keys_before_validation=False,
            remove_assoc_proxy_keys_before_validation=False, input_schema_modifier=None,
            update_only=False, create_only=False,
            skip_pre_processors=False, skip_post_processors=False):
        super(BatchSave, self).__init__(entity=entity)
        self.url = url
        self.view_function = view_function
        self.query_modifier = query_modifier
        self.permitted_object_getter = permitted_object_getter
        self.unique_identifier_fields = unique_identifier_fields
        self.result_saving_instance_model = result_saving_instance_model
        self.result_saving_instance_getter = result_saving_instance_getter
        self.run_as_async_task = run_as_async_task
        self.celery_worker = celery_worker
        self.update_only = update_only
        self.create_only = create_only
        self.skip_pre_processors = skip_pre_processors
        self.skip_post_processors = skip_post_processors
        self.before_save = before_save
        self.after_save = after_save
        self.extra_actions_before_save = extra_actions_before_save
        self.extra_actions_after_save = extra_actions_after_save
        self.response_dict_struct = response_dict_struct
        self.exception_handler = exception_handler
        self.access_checker = access_checker
        self.settable_fields = settable_fields
        self.non_settable_fields = non_settable_fields
        self.remove_property_keys_before_validation = remove_property_keys_before_validation
        self.remove_relationship_keys_before_validation = remove_relationship_keys_before_validation
        self.remove_assoc_proxy_keys_before_validation = remove_assoc_proxy_keys_before_validation
        self.input_schema_modifier = input_schema_modifier


class Entity(object):

    """This class represents a resource on which all the CRUD operations are defined.
    Think of it as a wrapper around the model. The same model can be exposed as different
    entities in different parts of the application

    Parameters
    ------------
    url_slug: str, Optional
        The common url slug which will be used to define the various CRUD endpoints
        defined on the entity. For example for an entity named Order, you can define
        the url_slug as orders

    model_class: class:flask_sqlalchemy.model.DefaultMeta
        The model for which the entity is being defined. This should be a Model class
        defined with FlaskSQLAlchemyBooster's model meta class as the base.

    name: str, optional
        An optional name for the entity. If it is not specified, the model name will be used
        as the name
    
    router: class:EntityRouter
        The router to which the entity is to be linked. To be specified if the entity is
        defined separately

    
    """

    def __init__(
            self, url_slug=None, model_class=None, name=None, router=None,
            permitted_operations=None, permitted_object_getter=None,
            forbidden_operations=None, endpoint_slug=None, input_schema_modifier=None,
            query_modifier=None, access_checker=None, exception_handler=None, response_dict_modifiers=None,
            id_attr=None, response_dict_struct=None, non_settable_fields=None, settable_fields=None,
            remove_relationship_keys_before_validation=False, remove_assoc_proxy_keys_before_validation=False,
            remove_property_keys_before_validation=False, enable_caching=False, cache_timeout=None,
            get=None, index=None, put=None, post=None, patch=None, delete=None, batch_save=None):
        self.model_class = model_class
        self.name = name or self.model_class.__name__
        self.router = router
        if self.router:
            if self not in self.router.routes:
                self.router.routes[self.url_slug] = self
        self.url_slug = url_slug
        self.permitted_object_getter = permitted_object_getter
        self.permitted_operations = permitted_operations
        self.forbidden_operations = forbidden_operations
        self.endpoint_slug = endpoint_slug
        self.input_schema_modifier = input_schema_modifier
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

        self.get = get
        if self.get and self.get.entity is None:
            self.get.init_entity(self)

        self.index = index
        if self.index and self.index.entity is None:
            self.index.init_entity(self)

        self.post = post
        if self.post and self.post.entity is None:
            self.post.init_entity(self)

        self.put = put
        if self.put and self.put.entity is None:
            self.put.init_entity(self)

        self.delete = delete
        if self.delete and self.delete.entity is None:
            self.delete.init_entity(self)

        self.patch = patch
        if self.patch and self.patch.entity is None:
            self.patch.init_entity(self)

        self.batch_save = batch_save
        if self.batch_save and self.batch_save.entity is None:
            self.batch_save.init_entity(self)
    

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



class EntitiesRouter(object):

    """
    Contains a collection of entities mapped to url routes. The router
    can be mounted on an app or a blueprint.

    Parameters
    -----------

    mount_point: Flask app or blueprint
        The app or blueprint on which the router is to be mounted. If this
        parameter is specified, the router will be mounted immediately. Or
        you can leave this unspecified and later call `router.mount_on(app_or_bp)`

    routes: dict
        A dictionary of url slugs mapped to entities like this
        {
            "orders": Entity(model_class=Order, index=Index(), get=Get(), post=Post(), put=Put()),
            "users": Entity(model_class=User, index=Index())
        }

    cache_handler: `class:FlaskCaching`
        A cache instance. Currently supports only FlaskCaching

    exception_handler: function, optional
        A function which accepts an exception and returns a json response

        Example:

        >>> def log_exception_and_return_json(e):
        >>>     return error_json(400, e.message)

    celery_worker: Celery, optional
        A celery worker which will be used to run the async batch save operation.

    register_schema_definition: bool, optional
        A bool flag which specifies whether the schema definition json needs to be registered.

    schema_def_url: str, Optional
        The url slug to be used to register the schema definition

    register_views_map: bool, optional
        A bool flag which specifies whether the views map json needs to be registered.

    views_map_url: str, Optional
        The url slug to be used to register the views map

    """

    def __init__(self,
        mount_point=None, routes=None, allow_unknown_fields=False, 
        cache_handler=None, exception_handler=None,
        tmp_folder_path="/tmp", permitted_operations=None,
        forbidden_operations=None, celery_worker=None,
        register_schema_definition=False, register_views_map=False,
        schema_def_url='/schema-def', views_map_url='/views-map',
        base_url=None
    ):

        self.schema_definition = {
            "models_registered_for_views": [],
            "model_schemas": {

            },
            "views": {

            }
        }
        self.routes = routes or {}
        for url_slug, entity in self.routes.items():
            if entity.url_slug is None:
                entity.url_slug = url_slug
            if entity.router is None:
                entity.router = self
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
        # self.registry = {}
        self.initialize_registry_entry()
        if mount_point:
            self.mount_point = mount_point
            self.mount_on(self.mount_point)

    def route(self, url_slug, entity):
        self.routes[url_slug] = entity
        if entity.url_slug is None:
            entity.url_slug = url_slug
        if entity.router is None:
            entity.router = self


    def get_registry_entry(self):
        return self.registry

    def initialize_registry_entry(self):
        self.registry = {
            "models_registered_for_views": [],
            "model_schemas": {

            },
            edk.OPERATION_MODIFIERS: {

            }
        }
    def mount_on(self, app_or_bp):
        self.mount_point = app_or_bp
        self.register_crud_routes()


    def to_dict(self):
        entities_map = {}
        for url_slug, entity in self.routes.items():
            entities_map[entity.name or entity.model_class] = entity.to_dict()
        return entities_map


    def register_crud_routes(
            self, allow_unknown_fields=False, cache_handler=None,
            exception_handler=None,
            tmp_folder_path="/tmp", celery_worker=None,
            register_schema_definition=True, register_views_map=True,
            schema_def_url='/schema-def', views_map_url='/views-map'):

        app_or_bp = self.mount_point
        registry = self.get_registry_entry()
        model_schemas = registry["model_schemas"]

        def populate_model_schema(model_class, entity=None):
            model_key = fetch_nested_key(entity, 'name') or model_class.__name__
            if model_class._input_data_schema_:
                input_schema = deepcopy(model_class._input_data_schema_)
            else:
                input_schema = model_class.generate_input_data_schema()
            if entity and callable(entity.input_schema_modifier):
                input_schema = entity.input_schema_modifier(
                    input_schema)
            model_schemas[model_key] = {
                "input_schema": input_schema,
                "output_schema": model_class.output_data_schema(),
                "accepted_data_structure": model_class.max_permissible_dict_structure()
            }
            for subcls in all_subclasses(model_class):
                if subcls.__name__ not in model_schemas:
                    model_schemas[subcls.__name__] = {
                        'is_a_polymorphically_derived_from': model_class.__name__,
                        'polymorphic_identity': subcls.__mapper_args__['polymorphic_identity']
                    }
            for rel in model_class.__mapper__.relationships.values():
                if rel.mapper.class_.__name__ not in model_schemas:
                    populate_model_schema(rel.mapper.class_)

        for url_slug, entity in self.routes.items():
            _model = entity.model_class
            _model_name = entity.name
            base_url = url_slug
            # base_url = _model_dict.get(edk.URL_SLUG)

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
                populate_model_schema(entity.model_class, entity)

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

            if entity.index:
                index_op = entity.index
                if index_op.enable_caching is not None:
                    enable_caching = index_op.enable_caching and cache_handler is not None
                cache_key_determiner = index_op.cache_key_determiner
                cache_timeout = index_op.cache_timeout or cache_timeout
                index_func = index_op.view_function or construct_index_view_function(
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

            if entity.get:
                get_op = entity.get
                if get_op.enable_caching is not None:
                    enable_caching = get_op.enable_caching and cache_handler is not None
                cache_key_determiner = get_op.cache_key_determiner
                cache_timeout = get_op.cache_timeout or cache_timeout
                get_func = get_op.view_function or construct_get_view_function(
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

            if entity.post:
                post_op = entity.post
                if callable(post_op.input_schema_modifier):
                    post_input_schema = post_op.input_schema_modifier(
                        deepcopy(model_default_input_schema))
                else:
                    post_input_schema = model_default_input_schema
                post_func = post_op.view_function or construct_post_view_function(
                    _model, post_input_schema,
                    entities_group=self,
                    pre_processors=post_op.before_save,
                    post_processors=post_op.after_save,
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

            if entity.put:
                put_op = entity.put
                if callable(put_op.input_schema_modifier):
                    put_input_schema = put_op.input_schema_modifier(
                        deepcopy(model_default_input_schema))
                else:
                    put_input_schema = model_default_input_schema
                put_func = put_op.view_function or construct_put_view_function(
                    _model, put_input_schema,
                    entities_group=self,
                    permitted_object_getter=put_op.permitted_object_getter or entity.permitted_object_getter,
                    pre_processors=put_op.before_save,
                    post_processors=post_op.after_save,
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

            if entity.patch:
                patch_op = entity.patch
                if callable(patch_op.input_schema_modifier):
                    patch_input_schema = patch_op.input_schema_modifier(
                        deepcopy(model_default_input_schema))
                else:
                    patch_input_schema = model_default_input_schema
                patch_func = patch_op.view_function or construct_patch_view_function(
                    _model, patch_input_schema,
                    pre_processors=patch_op.before_save,
                    commands=patch_op.commands,
                    post_processors=patch_op.after_save,
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

            if entity.delete:
                delete_op = entity.delete
                delete_func = delete_op.view_function or construct_delete_view_function(
                    _model,
                    query_constructor=delete_op.query_modifier or default_query_constructor,
                    pre_processors=delete_op.before_save,
                    permitted_object_getter=delete_op.permitted_object_getter or entity.permitted_object_getter,
                    post_processors=delete_op.after_save,
                    exception_handler=delete_op.exception_handler or default_exception_handler,
                    access_checker=delete_op.access_checker or default_access_checker)
                delete_url = delete_op.url or "/%s/<_id>" % base_url
                app_or_bp.route(
                    delete_url, methods=['DELETE'], endpoint='delete_%s' % endpoint_slug)(
                    delete_func)
                views[_model_name]['delete'] = {edk.URL: delete_url}

            if entity.batch_save:
                batch_save_op = entity.batch_save
                if callable(batch_save_op.input_schema_modifier):
                    batch_save_input_schema = batch_save_op.input_schema_modifier(
                        deepcopy(model_default_input_schema))
                else:
                    batch_save_input_schema = model_default_input_schema
                batch_save_func = batch_save_op.view_function or construct_batch_save_view_function(
                    _model, batch_save_input_schema,
                    app_or_bp=app_or_bp,
                    pre_processors_for_post=fetch_nested_key(entity, 'post.before_save'),
                    pre_processors_for_put=fetch_nested_key(entity, 'put.before_save'),
                    post_processors_for_post=fetch_nested_key(entity, 'post.after_save'),
                    post_processors_for_put=fetch_nested_key(entity, 'put.before_save'),
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
                    run_as_async_task=batch_save_op.run_as_async_task,
                    update_only=batch_save_op.update_only, create_only=batch_save_op.create_only,
                    skip_pre_processors=batch_save_op.skip_pre_processors,
                    skip_post_processors=batch_save_op.skip_post_processors
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


