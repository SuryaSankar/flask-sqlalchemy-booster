from __future__ import absolute_import
from flask_sqlalchemy import Model
from sqlalchemy.ext.associationproxy import AssociationProxy, AssociationProxyInstance
from sqlalchemy.orm import class_mapper
from toolspy import all_subclasses
from ..query_booster import QueryBooster
from .queryable_mixin import QueryableMixin
from .dictizable_mixin import DictizableMixin
from ..utils import get_rel_from_key, get_rel_class_from_key, attr_is_a_property
from sqlalchemy.ext.hybrid import hybrid_property
import six


class ModelBooster(Model, QueryableMixin, DictizableMixin):

    session = None

    query_class = QueryBooster

    def serial_key(self, key):
        return self.__modified_keys__.get(key, key)

    @classmethod
    def is_property_attr(cls, attr):
        return attr_is_a_property(cls, attr)

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
            keys += list(c.__dict__.keys())
        keys += list(cls.__dict__.keys())
        return keys

    @classmethod
    def dict_with_parent_class_fields(cls):
        result = {}
        for c in cls.parents():
            for k, v in six.iteritems(c.__dict__):
                result[k] = v
        for k, v in six.iteritems(cls.__dict__):
            result[k] = v
        return result    

    @classmethod
    def parent_with_column(cls, clmn):
        for p in cls.parents():
            if clmn in list(p.__table__.columns.keys()):
                return p
        return None

    @classmethod
    def property_keys(cls):
        return [k for k in cls.all_keys() if isinstance(
            getattr(cls, k), property)]

    @classmethod
    def association_proxy_keys(cls, include_parent_classes=True):
        keys_dict = cls.dict_with_parent_class_fields() if include_parent_classes else cls.__dict__
        assoc_keys = []
        for k, v in six.iteritems(keys_dict):
            if isinstance(v, AssociationProxy) and not k.startswith("_AssociationProxy_"):
                assoc_keys.append(k)
        return assoc_keys

    @classmethod
    def association_proxy_keys_dict(cls, include_parent_classes=True):
        keys_dict = cls.dict_with_parent_class_fields() if include_parent_classes else cls.__dict__
        return { 
            k: v for k, v in six.iteritems(keys_dict)
            if isinstance(v, AssociationProxy) and
            not k.startswith("_AssociationProxy_")
        }

    # @classmethod
    # def association_proxy_keys(cls, include_parent_classes=True):
    #     result = []
    #     keys = cls.all_keys() if include_parent_classes else cls.__dict__.keys()
    #     for k in keys:
    #         try:
    #             if isinstance(getattr(cls, k), AssociationProxyInstance) and not k.startswith("_AssociationProxy_"):
    #                 result.append(k)
    #         except:
    #             continue
    #     return result

    @classmethod
    def column_keys(cls):
        return [c.key for c in class_mapper(cls).columns]

    @classmethod
    def relationship_keys(cls):
        return [r.key for r in cls.__mapper__.relationships]

    @classmethod
    def hybrid_property_keys(cls):
        return [k for k in cls.all_keys() if hasattr(getattr(cls, k), 'descriptor') and isinstance(
            getattr(cls, k).descriptor, hybrid_property)]

    @classmethod
    def settable_hybrid_property_keys(cls):
        return [k for k in cls.hybrid_property_keys() if callable(getattr(cls, k).setter)]        

    @classmethod
    def all_settable_keys(cls):
        return cls.column_keys() + cls.relationship_keys() + cls.association_proxy_keys() + cls.settable_hybrid_property_keys()

    @classmethod
    def col_assoc_proxy_keys(cls):
        result = []
        for k, assoc_proxy in six.iteritems(cls.association_proxy_keys_dict()):
            assoc_rel_class = get_rel_class_from_key(cls, assoc_proxy.target_collection)
            if assoc_proxy.value_attr in list(class_mapper(assoc_rel_class).columns.keys()):
                result.append(k)
        return result

    @classmethod
    def rel_assoc_proxy_keys(cls):
        result = []
        for k, assoc_proxy in six.iteritems(cls.association_proxy_keys_dict()):
            assoc_rel_class = get_rel_class_from_key(cls, assoc_proxy.target_collection)
            if assoc_proxy.value_attr in list(class_mapper(assoc_rel_class).relationships.keys()):
                result.append(k)
        return result

    @classmethod
    def prop_assoc_proxy_keys(cls):
        result = []
        for k, assoc_proxy in six.iteritems(cls.association_proxy_keys_dict()):
            assoc_rel_class = get_rel_class_from_key(cls, assoc_proxy.target_collection)
            if assoc_rel_class.is_property_attr(assoc_proxy.value_attr):
                result.append(k)
        return result

    # @classmethod
    # def col_assoc_proxy_keys(cls):
    #     result = []
    #     for k in cls.association_proxy_keys():
    #         assoc_proxy = getattr(cls, k)
    #         assoc_rel = next(
    #             r for r in cls.__mapper__.relationships
    #             if r.key == assoc_proxy.target_collection)
    #         assoc_rel_class = assoc_rel.mapper.class_
    #         if assoc_proxy.value_attr in assoc_rel_class.__mapper__.columns.keys():
    #             result.append(k)
    #     return result

    # @classmethod
    # def rel_assoc_proxy_keys(cls):
    #     result = []
    #     for k in cls.association_proxy_keys():
    #         assoc_proxy = getattr(cls, k)
    #         assoc_rel = next(
    #             r for r in cls.__mapper__.relationships
    #             if r.key == assoc_proxy.target_collection)
    #         assoc_rel_class = assoc_rel.mapper.class_
    #         if assoc_proxy.value_attr in assoc_rel_class.__mapper__.relationships.keys():
    #             result.append(k)
    #     return result

    @classmethod
    def subclass(cls, pm_identity):
        mapper = class_mapper(cls).polymorphic_map.get(pm_identity)
        if mapper is None:
            return None
        return mapper.class_

    @classmethod
    def all_subclasses_with_separate_tables(cls):
        subcls = []
        all_scs = [cls] + all_subclasses(cls)
        seen_tables = []

        for sc in all_scs:
            if sc.__tablename__ not in seen_tables:
                seen_tables.append(sc.__tablename__)
                subcls.append(sc)
        return subcls

