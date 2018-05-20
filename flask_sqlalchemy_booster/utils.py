from sqlalchemy.ext.associationproxy import (
    _AssociationDict, _AssociationList, _AssociationSet)
from sqlalchemy.orm.collections import (
    InstrumentedList, MappedCollection)
from sqlalchemy.orm import class_mapper
from toolspy import flatten, all_subclasses, remove_duplicates
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
import os

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

def nullify_empty_values_in_dict(d):
    for k in d.keys():
        if d[k] == '':
            d[k] = None
    return d

def save_file_from_request(_file, location=None):
    filename = "%s_%s_%s" % (datetime.utcnow().strftime("%Y%m%d_%H%M%S%f"),
                             uuid.uuid4().hex[0:6],
                             secure_filename(_file.filename))
    file_path = os.path.join(location, filename)
    _file.save(file_path)
    return file_path