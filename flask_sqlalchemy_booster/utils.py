from sqlalchemy.ext.associationproxy import (
    _AssociationDict, _AssociationList)
from sqlalchemy.orm.collections import (
    InstrumentedList, MappedCollection)


def is_list_like(rel_instance):
    return (isinstance(rel_instance, list) or isinstance(
        rel_instance, _AssociationList) or isinstance(
        rel_instance, InstrumentedList))


def is_dict_like(rel_instance):
    return (isinstance(rel_instance, dict) or isinstance(
        rel_instance, _AssociationDict) or isinstance(
        rel_instance, MappedCollection))
