.. _howto

How To Use
==========

Since it just subclasses Flask-SQLAlchemy's Model class, the usage is entirely similar.

Set up Flask-SQLAlchemy related configuration keys to set up the database.

Then create a db instance like this::

	from flask.ext.sqlalchemy_booster import FlaskSQLAlchemyBooster
	db = FlaskSQLAlchemyBooster()

You can then subclass the `db.Model` class to create your model classes::

	class User(db.Model):
	    id = db.Column(db.Integer, primary_key=True, unique=True)
	    email = db.Column(db.String(100), unique=True)
	    password = db.Column(db.String(100))
	    name = db.Column(db.String(100))
	    active = db.Column(db.Boolean())

	class Order(db.Model):
	    id = db.Column(db.Integer, primary_key=True, unique=True)
    	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

