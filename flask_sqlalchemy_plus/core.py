from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy import (
    _QueryProperty, _BoundDeclarativeMeta)
from .queryplus import QueryPlus
from sqlalchemy.ext.declarative import declarative_base
from .modelplus import ModelPlus


class QueryPropertyPlus(_QueryProperty):
    """Subclassed to add the cls attribute to a query instance.

    This is useful in instances when we need to find the class
    of the model being queried when provided only with a query
    object
    """

    def __get__(self, obj, type_):
        query = super(QueryPropertyPlus, self).__get__(obj, type_)
        if query:
            query.cls = type_
        return query


class FlaskSQLAlchemyPlus(SQLAlchemy):
    """Sets the Model class to ModelPlus, providing all the methods
    defined on ModelPlus

    Examples
    --------

    >>> db = FlaskSQLAlchemyPlus()

    >>> class User(db.Model):
            id = db.Column(db.Integer, primary_key=True, unique=True)
            email = db.Column(db.String(100), unique=True)
            password = db.Column(db.String(100))
            name = db.Column(db.String(100))
            contact_number = db.Column(db.String(20))

    >>> User.all()

    >>> u = User.first()

    >>> u.todict()

    """

    def __init__(self, **kwargs):
        super(FlaskSQLAlchemyPlus, self).__init__(**kwargs)
        self.Query = QueryPlus

    def make_declarative_base(self):

        base = declarative_base(cls=ModelPlus, name='Model',
                                metaclass=_BoundDeclarativeMeta)
        base.query = QueryPropertyPlus(self)
        base.session = self.session
        return base
