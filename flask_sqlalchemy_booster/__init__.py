"""flask_sqlalchemy_booster

A wrapper over Flask-SQLAlchemy

"""

from .core import FlaskSQLAlchemyBooster, FlaskBooster
from .model_boosters import ModelBooster, QueryBooster
from .view_boosters import crud_api_view, responses
from .view_boosters.crud_api_view import register_crud_routes_for_models
from .json_encoder import json_encoder
from .json_columns import JSONEncodedStruct, MutableDict, MutableList
from .schema_generators import generate_input_data_schema
