from flask_sqlalchemy import Model
from .query_booster import QueryBooster
from .queryable_mixin import QueryableMixin
from .dictizable_mixin import DictizableMixin
from sqlalchemy.ext.associationproxy import AssociationProxy
from sqlalchemy.orm import class_mapper


class ModelBooster(Model, QueryableMixin, DictizableMixin):

    session = None

    query_class = QueryBooster

    #################################################################
    # Following methods are helpers used for older implementation of
    # to_serializable_dict. Not required anymore. But might be useful
    # in some future cases. Keeping them anyway
    ##################################################################

    def serial_key(self, key):
        return self.__modified_keys__.get(key, key)

    @classmethod
    def parents(cls):
        result = []
        for c in cls.mro():
            if(c != object and c != Model and c != QueryableMixin and
                    c != DictizableMixin and c != ModelBooster and c != cls):
                result.append(c)
        return result

    @classmethod
    def all_keys(cls):
        keys = []
        for c in cls.parents():
            keys += c.__dict__.keys()
        keys += cls.__dict__.keys()
        return keys

    @classmethod
    def parent_with_column(cls, clmn):
        for p in cls.parents():
            if clmn in p.__table__.columns.keys():
                return p
        return None

    @classmethod
    def property_keys(cls):
        return [k for k in cls.all_keys() if isinstance(
            getattr(cls, k), property)]

    @classmethod
    def association_proxy_keys(cls, include_parent_classes=True):
        result = []
        keys = cls.all_keys() if include_parent_classes else cls.__dict__.keys()
        for k in keys:
            try:
                if isinstance(getattr(cls, k), AssociationProxy):
                    result.append(k)
            except:
                continue
        return result

    @classmethod
    def relationship_keys(cls):
        return map(lambda r: r.key, cls.__mapper__.relationships)

    @classmethod
    def col_assoc_proxy_keys(cls):
        result = []
        for k in cls.association_proxy_keys():
            assoc_proxy = getattr(cls, k)
            assoc_rel = next(
                r for r in cls.__mapper__.relationships
                if r.key == assoc_proxy.target_collection)
            assoc_rel_class = assoc_rel.mapper.class_
            if assoc_proxy.value_attr in assoc_rel_class.__mapper__.columns.keys():
                result.append(k)
        return result

    @classmethod
    def rel_assoc_proxy_keys(cls):
        result = []
        for k in cls.association_proxy_keys():
            assoc_proxy = getattr(cls, k)
            assoc_rel = next(
                r for r in cls.__mapper__.relationships
                if r.key == assoc_proxy.target_collection)
            assoc_rel_class = assoc_rel.mapper.class_
            if assoc_proxy.value_attr in assoc_rel_class.__mapper__.relationships.keys():
                result.append(k)
        return result

    @classmethod
    def subclass(cls, pm_identity):
        mapper = class_mapper(cls).polymorphic_map.get(pm_identity)
        if mapper is None:
            return None
        return mapper.class_
