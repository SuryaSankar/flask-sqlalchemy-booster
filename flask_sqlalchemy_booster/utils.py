from __future__ import absolute_import
from sqlalchemy.ext.associationproxy import (
    _AssociationDict, _AssociationList, _AssociationSet)
from sqlalchemy.orm.collections import (
    InstrumentedList, MappedCollection)
from sqlalchemy.orm import class_mapper
from toolspy import flatten, all_subclasses, remove_duplicates, boolify
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
import os
from sqlalchemy.sql import sqltypes
from sqlalchemy import func
import dateutil.parser
from decimal import Decimal
import six
from contextlib import contextmanager


@contextmanager
def session_scope(session_creator):
    """Provide a transactional scope around a series of operations."""
    session = session_creator()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


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
        list(class_mapper(model_cls).columns.items()) +
        flatten(
            [list(class_mapper(subcls).columns.items())
             for subcls in all_subclasses(model_cls)]
        )
    )


def all_rels_including_subclasses(model_cls):
    return remove_duplicates(
        list(class_mapper(model_cls).relationships.items()) +
        flatten(
            [list(class_mapper(subcls).relationships.items())
             for subcls in all_subclasses(model_cls)]
        )
    )

def nullify_empty_values_in_dict(d):
    for k in d.keys():
        if d[k] == '':
            d[k] = None
    return d

def remove_empty_values_in_dict(d):
    for k in d.keys():
        if d[k] == '':
            del d[k]
    return d

def save_file_from_request(_file, location=None):
    filename = "{}_{}_{}".format(
        datetime.utcnow().strftime("%Y%m%d_%H%M%S%f"),
        uuid.uuid4().hex[0:6],
        secure_filename(_file.filename))
    file_path = os.path.join(location, filename)
    _file.save(file_path)
    return file_path

def type_coerce_value(column_type, value):
    if value is None:
        return None
    if isinstance(value, six.text_type) or isinstance(value, str):
        if value.lower() == 'none' or value.lower() == 'null' or value.strip() == '':
            return None
    if column_type is sqltypes.Integer:
        value = int(value)
    elif column_type is sqltypes.Numeric:
        value = Decimal(value)
    elif column_type is sqltypes.Boolean:
        value = boolify(value)
    elif column_type is sqltypes.DateTime:
        value = dateutil.parser.parse(value)
    elif column_type is sqltypes.Date:
        value = dateutil.parser.parse(value).date()
    return value

def convert_to_proper_types(data, model_class):
    columns = getattr(
        getattr(model_class, '__mapper__'),
        'columns')
    for attr_name, value in data.items():
        if attr_name in columns:
            column_type = type(
                columns[attr_name].type)
            data[attr_name] = type_coerce_value(column_type, value)
    return data

def cast_as_column_type(value, col):
    col_type = type(col.type)
    return type_coerce_value(col_type, value)


def tz_str(mins):
    prefix = "+" if mins >= 0 else "-"
    return "%s%02d:%02d" % (prefix, abs(mins) / 60, abs(mins) % 60)

def tz_convert(datetime_col, timedelta_mins):
    GMT_TZ_STR = '+00:00'
    return func.convert_tz(datetime_col, GMT_TZ_STR, tz_str(timedelta_mins))

def tz_converted_date(datetime_col, timedelta_mins):
    return func.date(tz_convert(datetime_col, timedelta_mins))


def get_rel_from_key(parent_class, rel_key):
    return next(
        r for r in class_mapper(parent_class).relationships
        if r.key == rel_key)

def get_rel_class_from_key(parent_class, rel_key):
    return get_rel_from_key(parent_class, rel_key).mapper.class_

def attr_is_a_property(klass, attr):
    return hasattr(klass, attr) and isinstance(getattr(klass, attr), property)
