from __future__ import absolute_import
from sqlalchemy.sql import sqltypes
from schemalite.validators import is_a_type_of
from decimal import Decimal
from datetime import datetime, date
from .json_columns import JSONEncodedStruct
import six


def generate_input_data_schema(model_cls, seen_classes=None, required=None, forbidden=None, post_processor=None):
    if seen_classes is None:
        seen_classes = []
    if required is None:
        required = []
    if forbidden is None:
        forbidden = []
    seen_classes.append(model_cls)
    schema = {
        "fields": {
        }
    }
    for col_name, col in model_cls.__mapper__.columns.items():
        if col_name not in forbidden:
            schema["fields"][col_name] = {
                "required": col_name in required,
                "validators": []
            }
            if type(col.type) == JSONEncodedStruct:
                schema["fields"][col_name]["type"] = col.type.mutable_type
                if col.type.mutable_type == list and col.type.item_type is not None:
                    schema["fields"][col_name]["list_item_type"] = col.type.item_type
            else:
                type_mapping = {
                    sqltypes.Integer: int,
                    sqltypes.Numeric: (Decimal, float),
                    sqltypes.DateTime: datetime,
                    sqltypes.Date: date,
                    sqltypes.Unicode: (six.text_type, str),
                    sqltypes.UnicodeText: (six.text_type, str),
                    sqltypes.String: (six.text_type, str),
                    sqltypes.Text: (six.text_type, str),
                    sqltypes.Boolean: bool,
                }
                schema["fields"][col_name]["type"] = type_mapping[type(col.type)]
                # schema["fields"][col_name]["validators"].append(
                #     is_a_type_of(*type_mapping[type(col.type)]))
    for rel_name, rel in model_cls.__mapper__.relationships.items():
        if rel_name not in forbidden and rel.mapper.class_ not in seen_classes:
            schema["fields"][rel_name] = {
                "required": col_name in required,
                "validators": [],
                "type": "list" if rel.uselist else 'dict'
            }
            if rel.uselist:
                schema["fields"][rel_name]["list_item_type"] = dict
                schema["fields"][rel_name]["list_item_schema"] = generate_input_data_schema(
                    rel.mapper.class_,
                    seen_classes)
            else:
                schema["fields"][rel_name]["dict_schema"] = generate_input_data_schema(
                    rel.mapper.class_,
                    seen_classes)
    if post_processor and callable(post_processor):
        post_processor(schema)
    return schema
