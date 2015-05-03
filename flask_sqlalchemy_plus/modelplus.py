from sqlalchemy.ext.associationproxy import AssociationProxy
import json
from flask_sqlalchemy import Model
from itertools import chain
from sqlalchemy import func
from toolspy import (
    place_nulls, subdict, deep_group,
    remove_and_mark_duplicate_dicts)
from datetime import datetime
from sqlalchemy.ext.associationproxy import (
    _AssociationDict, _AssociationList)
from sqlalchemy.orm.collections import (
    InstrumentedList, MappedCollection)
from .queryplus import QueryPlus


def dthandler(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    else:
        try:
            return json.JSONEncoder().default(obj)
        except:
            return str(obj)


def serialized_list(olist, rels_to_expand=[]):
    return map(
        lambda o: o.todict(
            rels_to_expand=rels_to_expand),
        olist)


def is_list_like(rel_instance):
    return (isinstance(rel_instance, list) or isinstance(
        rel_instance, _AssociationList) or isinstance(
        rel_instance, InstrumentedList))


def is_dict_like(rel_instance):
    return (isinstance(rel_instance, dict) or isinstance(
        rel_instance, _AssociationDict) or isinstance(
        rel_instance, MappedCollection))


class ModelPlus(Model):

    # The scalar attributes to serialize.
    _attrs_to_serialize_ = []

    # Change the name of any attribute to anything else
    _key_modifications_ = {}

    _rels_to_serialize_ = []
    _rels_to_expand_ = []

    _group_listrels_by_ = {}

    __no_overwrite__ = []

    session = None

    query_class = QueryPlus

    @classmethod
    def is_list_attribute(cls, rel):
        if rel in cls.__mapper__.relationships:
            return cls.__mapper__.relationships[rel].uselist
        rel_instance = getattr(cls, rel)
        if isinstance(rel_instance, AssociationProxy):
            return cls.__mapper__.relationships[
                rel_instance.target_collection].uselist
        return False

    def to_serializable_dict(self, attrs_to_serialize=None,
                             rels_to_expand=None,
                             rels_to_serialize=None,
                             key_modifications=None):
        """
        Just an alias for some functions which might still use old name
        """
        return self.todict(
            attrs_to_serialize=attrs_to_serialize,
            rels_to_expand=rels_to_expand, rels_to_serialize=rels_to_serialize,
            key_modifications=key_modifications)

    # Version 5.0
    def todict(self, attrs_to_serialize=None,
               rels_to_expand=None,
               rels_to_serialize=None,
               group_listrels_by=None,
               key_modifications=None):
        # The most important method in the code base. Gets called
        # for every request.

        # Never replace the following code by the (attrs = attrs or
        # self._attrs_) idiom. Python considers empty list as false. So
        # even if you pass an empty list, it will take self._x_ value. But
        # we don't want that as the empty list is what we use to end
        # the recursion
        attrs_to_serialize = (
            self._attrs_to_serialize_ if attrs_to_serialize is None
            else attrs_to_serialize)
        rels_to_serialize = (
            self._rels_to_serialize_ if rels_to_serialize is None
            else rels_to_serialize)
        rels_to_expand = (
            self._rels_to_expand_ if rels_to_expand is None
            else rels_to_expand)
        # assoc_proxies_to_expand = (
        #     self._assoc_proxies_to_expand_ if assoc_proxies_to_expand is None
        #     else assoc_proxies_to_expand)
        key_modifications = (
            self._key_modifications_ if key_modifications is None
            else key_modifications)
        group_listrels_by = (
            self._group_listrels_by_ if group_listrels_by is None
            else group_listrels_by)
        # Convert rels_to_expand to a dictionary
        rels_to_expand_dict = {}
        for rel in rels_to_expand:
            partitioned_rels = rel.partition('.')
            if partitioned_rels[0] not in rels_to_expand_dict:
                rels_to_expand_dict[partitioned_rels[0]] = (
                    [partitioned_rels[-1]] if partitioned_rels[-1]
                    else [])
            else:
                if partitioned_rels[-1]:
                    rels_to_expand_dict[partitioned_rels[0]].append(
                        partitioned_rels[-1])

        # # Convert grouplistrelsby to a dict
        # group_listrels_dict = {}
        # for rel_to_group, grouping_keys in group_listrels_by.iteritems():
        #     partitioned_rel_to_group = rel_to_group.partition('.')
        #     if partitioned_rel_to_group[0] not in group_listrels_dict:
        #         group_listrels_dict[partitioned_rel_to_group[0]] = (
        #             {partitioned_rel_to_group[-1]: grouping_keys}
        #             if partitioned_rel_to_group[-1] else grouping_keys)
        #     else:
        #         if partitioned_rel_to_group[-1]:
        #             group_listrels_dict[
        #                 partitioned_rel_to_group[0]][
        #                     partitioned_rel_to_group[-1]] = grouping_keys

        # Serialize attrs
        result = self.serialize_attrs(*attrs_to_serialize)

        # Serialize rels
        if len(rels_to_serialize) > 0:
            for rel, id_attr in rels_to_serialize:
                rel_obj = getattr(self, rel, None)
                if rel_obj is not None:
                    if is_list_like(rel_obj):
                        if (group_listrels_by is not None and
                                rel in group_listrels_by):
                            result[rel] = deep_group(
                                rel_obj,
                                attr_to_show=id_attr,
                                keys=group_listrels_by[rel]
                            )
                        else:
                            result[rel] = [getattr(item, id_attr)
                                           for item in rel_obj]
                    elif is_dict_like(rel_obj):
                        result[rel] = {k: getattr(v, id_attr)
                                       for k, v in rel_obj.iteritems()}
                    else:
                        result[rel] = getattr(rel_obj, id_attr)

        # Expand some rels
        for rel, child_rels in rels_to_expand_dict.iteritems():
            rel_obj = getattr(self, rel, None)
            if rel_obj is not None:
                if is_list_like(rel_obj):
                    if (group_listrels_by is not None and
                            rel in group_listrels_by):
                        result[rel] = deep_group(
                            rel_obj,
                            keys=group_listrels_by[rel], serializer='todict',
                            serializer_kwargs={'rels_to_expand': child_rels}
                        )
                    else:
                        result[rel] = [i.todict(rels_to_expand=child_rels)
                                       if hasattr(i, 'todict') else i
                                       for i in rel_obj]
                        # result[rel] = serialized_list(
                        #     rel_obj, rels_to_expand=child_rels)
                elif is_dict_like(rel_obj):
                    result[rel] = {k: v.todict()
                                   if hasattr(v, 'todict') else v
                                   for k, v in rel_obj.iteritems()}
                else:
                    result[rel] = rel_obj.todict(
                        rels_to_expand=child_rels) if hasattr(
                        rel_obj, 'todict') else rel_obj

        for key, mod_key in key_modifications.items():
            if key in result:
                result[mod_key] = result.pop(key)

        return result

    def serialize_attrs(self, *args):
        return dict([(a, getattr(self, a)) for a in args])

    def tojson(self, attrs_to_serialize=None,
               rels_to_expand=None,
               rels_to_serialize=None,
               key_modifications=None):
        return json.dumps(
            self.todict(
                attrs_to_serialize=attrs_to_serialize,
                rels_to_expand=rels_to_expand,
                rels_to_serialize=rels_to_serialize,
                key_modifications=key_modifications),
            default=dthandler)

    def update(self, **kwargs):
        kwargs = self._preprocess_params(kwargs)
        for key, value in kwargs.iteritems():
            if key not in self.__no_overwrite__:
                setattr(self, key, value)
        try:
            self.session.commit()
            return self
        except Exception as e:
            self.session.rollback()
            raise e

    def commit(self):
        self.session.commit()

    def save(self):
        self.session.add(self)
        self.session.commit()

    def delete(self, commit=True):
        self.session.delete(self)
        if commit:
            self.session.commit

    def _isinstance(self, model, raise_error=True):
        """Checks if the specified model instance matches the service's model.
        By default this method will raise a `ValueError` if the model is not of
        expected type.

        :param model: the model instance to check
        :param raise_error: flag to raise an error on a mismatch
        """
        rv = isinstance(model, self.__model__)
        if not rv and raise_error:
            raise ValueError('%s is not of type %s' % (model, self.__model__))
        return rv

    @classmethod
    def rollback_session(cls):
        cls.session.rollback()

    @classmethod
    def _preprocess_params(cls, kwargs):
        """Returns a preprocessed dictionary of parameters. Used by default
        before creating a new instance or updating an existing instance.

        :param kwargs: a dictionary of parameters
        """
        kwargs.pop('csrf_token', None)
        return kwargs

    @classmethod
    def filter_by(cls, **kwargs):
        """Returns a list of instances of the service's model filtered by the
        specified key word arguments.

        :param **kwargs: filter parameters
        """
        limit = kwargs.pop('limit', None)
        reverse = kwargs.pop('reverse', False)
        q = cls.query.filter_by(**kwargs)
        if reverse:
            q = q.order_by(cls.id.desc())
        if limit:
            q = q.limit(limit)
        return q

    @classmethod
    def filter(cls, *criterion, **kwargs):
        limit = kwargs.pop('limit', None)
        reverse = kwargs.pop('reverse', False)
        q = cls.query.filter_by(**kwargs).filter(*criterion)
        if reverse:
            q = q.order_by(cls.id.desc())
        if limit:
            q = q.limit(limit)
        return q

    @classmethod
    def count(cls, *criterion, **kwargs):
        if criterion or kwargs:
            return cls.filter(
                *criterion,
                **kwargs).count()
        else:
            return cls.query.count()

    @classmethod
    def all(cls, *criterion, **kwargs):
        """Returns a list of instances of the service's model filtered by the
        specified key word arguments.

        :param **kwargs: filter parameters
        """
        return cls.filter(*criterion, **kwargs).all()

    @classmethod
    def first(cls, *criterion, **kwargs):
        """Returns the first instance found of the service's model filtered by
        the specified key word arguments.

        :param **kwargs: filter parameters
        """
        return cls.filter(*criterion, **kwargs).first()

    @classmethod
    def one(cls, *criterion, **kwargs):
        return cls.filter(*criterion, **kwargs).one()

    @classmethod
    def last(cls, *criterion, **kwargs):
        kwargs['reverse'] = True
        return cls.first(*criterion, **kwargs)

    @classmethod
    def new(cls, **kwargs):
        """Returns a new, unsaved instance of the service's model class.

        :param **kwargs: instance parameters
        """
        return cls(**cls._preprocess_params(kwargs))

    @classmethod
    def add(cls, model, commit=True):
        if not isinstance(model, cls):
            raise ValueError('%s is not of type %s' (model, cls))
        cls.session.add(model)
        try:
            if commit:
                cls.session.commit()
            return model
        except:
            cls.session.rollback()
            raise

    @classmethod
    def add_all(cls, models, commit=True, check_type=False):
        if check_type:
            for model in models:
                if not isinstance(model, cls):
                    raise ValueError('%s is not of type %s' (model, cls))
        cls.session.add_all(models)
        try:
            if commit:
                cls.session.commit()
            return models
        except:
            cls.session.rollback()
            raise

    @classmethod
    def _get(cls, key, keyval, user_id=None):
        result = cls.query.filter(
            getattr(cls, key) == keyval)
        if user_id and hasattr(cls, 'user_id'):
            result = result.filter(cls.user_id == user_id)
        return result.one()

    @classmethod
    def get(cls, keyval, key='id', user_id=None):
        """Returns an instance of the service's model with the specified id.
        Returns `None` if an instance with the specified id does not exist.

        :param id: the instance id
        """
        if (key in cls.__table__.columns
                and cls.__table__.columns[key].primary_key):
            if user_id and hasattr(cls, 'user_id'):
                return cls.query.filter_by(id=keyval, user_id=user_id).one()
            return cls.query.get(keyval)
        else:
            result = cls.query.filter(
                getattr(cls, key) == keyval)
            if user_id and hasattr(cls, 'user_id'):
                result = result.filter(cls.user_id == user_id)
            return result.one()

    @classmethod
    def get_all(cls, keyvals, key='id', user_id=None):
        if len(keyvals) == 0:
            return []
        resultset = cls.query.filter(getattr(cls, key).in_(keyvals))
        if user_id and hasattr(cls, 'user_id'):
            resultset = resultset.filter(cls.user_id == user_id)
        # We need the results in the same order as the input keyvals
        # So order by field in SQL
        resultset = resultset.order_by(
            func.field(getattr(cls, key), *keyvals))
        return place_nulls(key, keyvals, resultset.all())

    # @classmethod
    # def get_all(cls, ids, user_id=None):
    #     return cls._get_all('id', ids, user_id=user_id)

    @classmethod
    def get_or_404(cls, id):
        """Returns an instance of the service's model with the specified id or
        raises an 404 error if an instance with the specified id does not exist

        :param id: the instance id
        """
        return cls.query.get_or_404(id)

    @classmethod
    def create(cls, **kwargs):
        """Returns a new, saved instance of the service's model class.

        :param **kwargs: instance parameters
        """
        try:
            return cls.add(cls.new(**kwargs))
        except:
            cls.session.rollback()
            raise

    @classmethod
    def find_or_create(cls, **kwargs):
        """Checks if an instance already exists in db with these kwargs else
        returns a new, saved instance of the service's model class.

        :param **kwargs: instance parameters
        """
        keys = kwargs.pop('keys') if 'keys' in kwargs else []
        return cls.first(**subdict(kwargs, keys)) or cls.create(**kwargs)

    @classmethod
    def update_or_create(cls, **kwargs):
        keys = kwargs.pop('keys') if 'keys' in kwargs else []
        obj = cls.first(**subdict(kwargs, keys))
        if obj is not None:
            for key, value in kwargs.iteritems():
                if (key not in keys and
                        key not in cls.__no_overwrite__):
                    setattr(obj, key, value)
            try:
                cls.session.commit()
            except:
                cls.session.rollback()
                raise
        else:
            obj = cls.create(**kwargs)
        return obj

    @classmethod
    def create_all(cls, list_of_kwargs):
        try:
            return cls.add_all([
                cls.new(**kwargs) for kwargs in list_of_kwargs])
        except:
            cls.session.rollback()
            raise

    @classmethod
    def find_or_create_all(cls, list_of_kwargs, keys=[]):
        list_of_kwargs_wo_dupes, markers = remove_and_mark_duplicate_dicts(
            list_of_kwargs, keys)
        added_objs = cls.add_all([
            cls.first(**subdict(kwargs, keys)) or cls.new(**kwargs)
            for kwargs in list_of_kwargs_wo_dupes])
        result_objs = []
        iterator_of_added_objs = iter(added_objs)
        for idx in range(len(list_of_kwargs)):
            if idx in markers:
                result_objs.append(added_objs[markers[idx]])
            else:
                result_objs.append(next(
                    iterator_of_added_objs))
        return result_objs

    @classmethod
    def update_or_create_all(cls, list_of_kwargs, keys=[]):
        objs = []
        for kwargs in list_of_kwargs:
            obj = cls.first(**subdict(kwargs, keys))
            if obj is not None:
                for key, value in kwargs.iteritems():
                    if (key not in keys and
                            key not in cls.__no_overwrite__):
                        setattr(obj, key, value)
            else:
                obj = cls.new(**kwargs)
            objs.append(obj)
        try:
            return cls.add_all(objs)
        except:
            cls.session.rollback()
            raise

    @classmethod
    def build(cls, **kwargs):
        """Returns a new, added but unsaved instance of the service's model class.

        :param **kwargs: instance parameters
        """
        return cls.add(cls.new(**kwargs), commit=False)

    @classmethod
    def find_or_build(cls, **kwargs):
        """Checks if an instance already exists in db with these kwargs else
        returns a new, saved instance of the service's model class.

        :param **kwargs: instance parameters
        """
        return cls.first(**kwargs) or cls.build(**kwargs)

    @classmethod
    def new_all(cls, list_of_kwargs):
        return [cls.new(**kwargs) for kwargs in list_of_kwargs]

    @classmethod
    def build_all(cls, list_of_kwargs):
        return cls.add_all([
            cls.new(**kwargs) for kwargs in list_of_kwargs], commit=False)

    @classmethod
    def find_or_build_all(cls, list_of_kwargs):
        return cls.add_all([cls.first(**kwargs) or cls.new(**kwargs)
                            for kwargs in list_of_kwargs], commit=False)

    @classmethod
    def update_all(cls, *criterion, **kwargs):
        try:
            r = cls.query.filter(*criterion).update(kwargs, 'fetch')
            cls.session.commit()
            return r
        except:
            cls.session.rollback()
            raise

    @classmethod
    def get_and_update(cls, id, **kwargs):
        """Returns an updated instance of the service's model class.

        :param model: the model to update
        :param **kwargs: update parameters
        """
        model = cls.get(id)
        for k, v in cls._preprocess_params(kwargs).items():
            setattr(model, k, v)
        cls.session.commit()
        return model

    @classmethod
    def get_and_setattr(cls, id, **kwargs):
        """Returns an updated instance of the service's model class.

        :param model: the model to update
        :param **kwargs: update parameters
        """
        model = cls.get(id)
        for k, v in cls._preprocess_params(kwargs).items():
            setattr(model, k, v)
        return model

