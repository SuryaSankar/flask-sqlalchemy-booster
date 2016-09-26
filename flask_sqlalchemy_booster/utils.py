from sqlalchemy.ext.associationproxy import (
    _AssociationDict, _AssociationList, _AssociationSet)
from sqlalchemy.orm.collections import (
    InstrumentedList, MappedCollection)
from sqlalchemy.orm import class_mapper
from toolspy import flatten, all_subclasses, remove_duplicates


def is_list_like(rel_instance):
    return (isinstance(rel_instance, list) or isinstance(rel_instance, set)
            or isinstance(rel_instance, _AssociationList)
            or isinstance(rel_instance, _AssociationSet)
            or isinstance(rel_instance, InstrumentedList))


def is_dict_like(rel_instance):
    return (isinstance(rel_instance, dict) or isinstance(
        rel_instance, _AssociationDict) or isinstance(
        rel_instance, MappedCollection))


def all_cols_including_subclasses(model_cls):
    return remove_duplicates(
        class_mapper(model_cls).columns.items() +
        flatten(
            [class_mapper(subcls).columns.items()
             for subcls in all_subclasses(model_cls)]
        )
    )


def all_rels_including_subclasses(model_cls):
    return remove_duplicates(
        class_mapper(model_cls).relationships.items() +
        flatten(
            [class_mapper(subcls).relationships.items()
             for subcls in all_subclasses(model_cls)]
        )
    )