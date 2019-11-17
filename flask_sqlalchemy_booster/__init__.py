"""flask_sqlalchemy_booster

A wrapper over Flask-SQLAlchemy

"""

from __future__ import absolute_import
from .core import FlaskSQLAlchemyBooster, FlaskBooster
from .model_booster import ModelBooster
from .query_booster import QueryBooster
from .json_encoder import json_encoder
from .json_columns import JSONEncodedStruct, MutableDict, MutableList
from .schema_generators import generate_input_data_schema
from . import crud_api_view, responses
from .crud_api_view import register_crud_routes_for_models
from .interactive_shell import run_interactive_shell