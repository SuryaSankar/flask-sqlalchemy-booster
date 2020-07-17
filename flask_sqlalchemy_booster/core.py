from __future__ import absolute_import
from flask import Flask, g, request
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy import _QueryProperty
from sqlalchemy.ext.declarative import declarative_base
from .model_booster import ModelBooster
from .query_booster import QueryBooster
from .flask_client_booster import FlaskClientBooster
import bleach
from werkzeug.datastructures import MultiDict
from decimal import Decimal
import six
from flask.json import _json as json

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

    def __init__(self, *args, **kwargs):
        kwargs["model_class"] = ModelBooster
        kwargs["query_class"] = QueryBooster
        super(FlaskSQLAlchemyBooster, self).__init__(*args, **kwargs)
        # self.Query = QueryBooster

    def make_declarative_base(self, model, metadata=None):
        base = super(FlaskSQLAlchemyBooster, self).make_declarative_base(
            model, metadata)
        base.query = QueryPropertyWithModelClass(self)
        base.session = self.session
        return base

def _sanitize_object(obj):
    result = {}
    for k, v in obj.items():
        if isinstance(v, int) or isinstance(v, Decimal):
            result[k] = v
        elif not (isinstance(v, str) or isinstance(v, six.text_type)):
            result[k] = json.loads(bleach.clean(json.dumps(v)))
        else:
            result[k] = bleach.clean(v)
        if result[k] == '':
            result[k] = None
        # Making an assumption that there is no good usecase
        # for setting an empty string. This will help prevent
        # cases where empty string is sent because of client
        # not clearing form fields to null
    return result

def sanitize_args():
    if 'args' not in g:
        g.args = {}
    for arg, argv in request.args.items():
        g.args[arg] = bleach.clean(argv)

def sanitize_json():
    g.json = None
    json_data = request.get_json()
    if isinstance(json_data, dict):
        g.json = _sanitize_object(json_data)
    elif isinstance(json_data, list):
        g.json = [_sanitize_object(o) for o in json_data]
    else:
        g.json = None

def sanitize_form():
    if 'form' not in g:
        g.form = MultiDict(request.form)
    if request.form is not None:
        for k, v in request.form.items():
            g.form[k] = bleach.clean(v)
            if g.form[k] == '':
                g.form[k] = None

class FlaskBooster(Flask):
    test_client_class = FlaskClientBooster

    def __init__(self, *args, **kwargs):
        json_sanitizer = kwargs.pop('json_sanitizer', sanitize_json)
        args_sanitizer = kwargs.pop('args_sanitizer', sanitize_args)
        form_sanitizer = kwargs.pop('form_sanitizer', sanitize_form)

        super(FlaskBooster, self).__init__(*args, **kwargs)

        self.before_request_funcs.setdefault(None, []).append(json_sanitizer)
        self.before_request_funcs.setdefault(None, []).append(args_sanitizer)
        self.before_request_funcs.setdefault(None, []).append(form_sanitizer)

