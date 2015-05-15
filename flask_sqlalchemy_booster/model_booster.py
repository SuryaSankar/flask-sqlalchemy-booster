from flask_sqlalchemy import Model
from .query_booster import QueryBooster
from .queryable_mixin import QueryableMixin
from .dictizable_mixin import DictizableMixin


class ModelBooster(Model, QueryableMixin, DictizableMixin):

    session = None

    query_class = QueryBooster
