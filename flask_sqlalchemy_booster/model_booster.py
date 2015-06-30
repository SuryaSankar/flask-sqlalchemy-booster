from flask_sqlalchemy import Model
from .query_booster import QueryBooster
from .queryable_mixin import QueryableMixin
from .dictizable_mixin import DictizableMixin
from sqlalchemy.ext.associationproxy import AssociationProxy
import flask_sqlalchemy


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
    def association_proxy_keys(cls):
        return [k for k in cls.all_keys() if isinstance(
            getattr(cls, k), AssociationProxy)]

    @classmethod
    def relationship_keys(cls):
        return map(lambda r: r.key, cls.__mapper__.relationships)
