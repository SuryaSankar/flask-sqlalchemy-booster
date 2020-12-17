from toolspy.class_tools import set_instance_attr_vals, to_dict

class EntityOperation(object):
    def __init__(self, entity):
        self.entity = entity
        self.entity_group = entity.entity_group

    def to_dict(self):
        return to_dict(self)

class Get(EntityOperation):

    method = 'get'

    def __init__(self, entity):
        super(Get, self).__init__(entity)

class Index(EntityOperation):

    method = 'index'

    def __init__(self, entity):
        super(Index, self).__init__(entity)


class Post(EntityOperation):

    method = 'post'

    def __init__(self, entity):
        super(Post, self).__init__(entity)

class Put(EntityOperation):

    method = 'put'

    def __init__(self, entity):
        super(Put, self).__init__(entity)

class Patch(EntityOperation):

    method = 'patch'

    def __init__(self, entity):
        super(Patch, self).__init__(entity)

class Delete(EntityOperation):

    method = 'delete'

    def __init__(self, entity):
        super(Delete, self).__init__(entity)

class BatchSave(EntityOperation):

    method = 'batch_save'

    def __init__(self, entity):
        super(BatchSave, self).__init__(entity)


class Entity(object):
    def __init__(
            self, url_slug=None, model_class=None, entity_set=None, permitted_operations=None, 
            forbidden_operations=None, resource_name=None,
            query_constructor=None, access_checker=None, exception_handler=None, dict_post_processors=None,
            id_attr=None, dict_struct=None, fields_forbidden_from_being_setrinto=None, settable_fields=None,
            remove_relationship_keys_before_validation=False, remove_assoc_proxy_keys_before_validation=False,
            remove_property_keys_before_validation=False, enable_caching=False, cache_timeout=None):
        set_instance_attr_vals(self, locals())


    def to_dict(self):
        return to_dict(self)


class EntitiesGroup(object):
    all_operations = ['index', 'get', 'post', 'put', 'patch', 'delete', 'batch_save']

    def __init__(self,
        app_or_bp=None, allow_unknown_fields=False, cache_handler=None, exception_handler=None,
        tmp_folder_path="/tmp", permitted_operations=None,
        forbidden_operations=None, celery_worker=None,
        register_schema_definition=False, register_views_map=False,
        schema_def_url='/schema-def', views_map_url='/views-map',
        entities=None
    ):
        self.schema_definition = {
            "models_registered_for_views": [],
            "model_schemas": {

            },
            "views": {

            }
        }
        self.entities = entities
        self.cache_handler = cache_handler
        self.exception_handler = exception_handler
        self.permitted_operations = permitted_operations
        self.forbidden_operations = forbidden_operations
        if app_or_bp:
            self.initialize(app_or_bp)

    def initialize(self, app_or_bp):
        self.app_or_bp = app_or_bp

    def to_dict(self):
        entities_map = {}
        for entity in self.entities:
            entities_map[entity.model_class or entity.model_name] = entity.to_dict()
        return entities_map