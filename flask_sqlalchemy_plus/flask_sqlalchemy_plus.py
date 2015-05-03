from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy import (
    _QueryProperty, _BoundDeclarativeMeta)
from .queryplus import QueryPlus
from sqlalchemy.ext.declarative import declarative_base
from .modelplus import ModelPlus


# class SignallingSessionPlus(SignallingSession):
#     def __init__(self, db, autocommit=False, autoflush=True, **options):
#         super(SignallingSessionPlus, self).__init__(
#             db, autocommit, autoflush, **options)
#         self.plus_record = {}


class QueryPropertyPlus(_QueryProperty):

    def __get__(self, obj, type_):
        query = super(QueryPropertyPlus, self).__get__(obj, type_)
        if query:
            query.cls = type_
        return query


class SQLAlchemyPlus(SQLAlchemy):

    # def create_session(self, options):
    #     return SignallingSessionPlus(self, **options)

    def __init__(self, **kwargs):
        super(SQLAlchemyPlus, self).__init__(**kwargs)
        self.Query = QueryPlus

    def make_declarative_base(self):
        """Creates the declarative base."""

        base = declarative_base(cls=ModelPlus, name='Model',
                                metaclass=_BoundDeclarativeMeta)
        base.query = QueryPropertyPlus(self)
        base.session = self.session
        return base
