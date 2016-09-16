from sqlalchemy.sql import sqltypes
from schemalite.validators import is_a_type_of
from decimal import Decimal
from datetime import datetime, date
from .json_columns import JSONEncodedStruct


def generate_input_data_schema(model_cls, seen_classes=None, required=[], post_processor=None):
    if seen_classes is None:
        seen_classes = []
    seen_classes.append(model_cls)
    schema = {
        "fields": {
        }
    }
    for col_name, col in model_cls.__mapper__.columns.items():
        schema["fields"][col_name] = {
            "required": col_name in required,
            "validators": []
        }
        if type(col.type) == JSONEncodedStruct:
            schema["fields"][col_name]["validators"].append(
                is_a_type_of(col.type.mutable_type))
        else:
            type_mapping = {
                sqltypes.Integer: (int,),
                sqltypes.Numeric: (Decimal, float),
                sqltypes.DateTime: (datetime,),
                sqltypes.Date: (date,),
                sqltypes.Unicode: (unicode, str),
                sqltypes.UnicodeText: (unicode, str),
                sqltypes.String: (unicode, str),
                sqltypes.Text: (unicode, str),
                sqltypes.Boolean: (bool,)
            }
            schema["fields"][col_name]["validators"].append(
                is_a_type_of(*type_mapping[type(col.type)]))
    for rel_name, rel in model_cls.__mapper__.relationships.items():
        if rel.mapper.class_ not in seen_classes:
            schema["fields"][rel_name] = {
                "required": col_name in required,
                "validators": [],
                "schema": generate_input_data_schema(
                    rel.mapper.class_,
                    seen_classes)
            }
    if post_processor and callable(post_processor):
        post_processor(schema)
    return schema
