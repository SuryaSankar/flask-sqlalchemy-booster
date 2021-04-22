API
===


Core
----

.. automodule:: flask_sqlalchemy_booster.core
    :members:
    :show-inheritance:

ModelBooster
-------------
This is the `db.Model` class that you will use as the super class for your
Models. It has two sets of methods defined on it, apart from the ones 
already defined by FlaskSQLAlchemy.

.. autoclass:: flask_sqlalchemy_booster.queryable_mixin.QueryableMixin
    :members:

.. autoclass:: flask_sqlalchemy_booster.dictizable_mixin.DictizableMixin
    :members:

Responses
---------

.. automodule:: flask_sqlalchemy_booster.responses
    :members:

EntitiesRouter
--------------------------------

.. automodule:: flask_sqlalchemy_booster.entities_router
    :members:

