.. flask-sqlalchemy-booster documentation master file, created by
   sphinx-quickstart on Sat May 16 03:06:43 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Flask-SQLAlchemy-Booster
========================
Flask-SQLAlchemy-Booster is a collection of enhancements to the Flask-SQLAlchemy
library.

It replaces the Model class with a subclass that adds 
	1. Additional querying methods and
	2. Easily configurable `todict` methods and `tojson` methods for serializing objects.

It also provides some decorators and utility functions which can be used to easily generate JSON responses.

Features
--------

- Fully compatible with code written for Flask-SQLAlchemy. It will just transparently
  replace it with additional features.

- Simple api for most common querying operations::

	  >>> user = User.first()
	  >>> user2 = User.last()
	  >>> newcust = Customer.find_or_create(name="Alex", age=21, email="al@h.com")

- JSON response functions which can be dynamically configured via the GET request params allowing you to do things like::

		GET /api/customers?city~=Del&expand=shipments.country,user&sort=desc&limit=5

Contents
========

.. toctree::
   :maxdepth: 2

   install
   howto
   api



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

