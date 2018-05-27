from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy import _QueryProperty
from .query_booster import QueryBooster
from sqlalchemy.ext.declarative import declarative_base
from .model_booster import ModelBooster


class QueryPropertyWithModelClass(_QueryProperty):
    """Subclassed to add the cls attribute to a query instance.

    This is useful in instances when we need to find the class
    of the model being queried when provided only with a query
    object
    """

    def __get__(self, obj, type_):
        query = super(QueryPropertyWithModelClass, self).__get__(obj, type_)
        if query:
            # print "about to set query.model_class"
            query.model_class = type_
        return query


class FlaskSQLAlchemyBooster(SQLAlchemy):
    """Sets the Model class to ModelBooster, providing all the methods
    defined on ModelBooster.

    Examples
    --------

    >>> db = FlaskSQLAlchemyBooster()

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
        kwargs["model_class"] = ModelBooster
        kwargs["query_class"] = QueryBooster
        super(FlaskSQLAlchemyBooster, self).__init__(**kwargs)
        # self.Query = QueryBooster

    def make_declarative_base(self, model, metadata=None):
        print "calling make_declarative_base"
        base = super(FlaskSQLAlchemyBooster, self).make_declarative_base(
            model, metadata)
        base.query = QueryPropertyWithModelClass(self)
        base.session = self.session
        return base
