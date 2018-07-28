"""
Flask-SQLAlchemy-Booster
------------------------

Adds further methods to Flask-SQLAlchemy by subclassing the
Model class and adding

    1. Class methods to enable easy querying

    2. Methods to convert the model object to a JSON convertible
    dictionary.

"""

from setuptools import setup

setup(
    name='Flask-SQLAlchemy-Booster',
    version='0.5.3',
    description='Querying and JSON Response generation wrappers for Flask-SQLAlchemy',
    long_description='Allows querying on Model classes, supports several common query operations, allows JSONification of models and relations and provides a simple query language for dynamically fetching data',
    packages=['flask_sqlalchemy_booster'],
    include_package_data=True,
    install_requires=[
        "toolspy>=0.2.25",
        "Flask>=0.10.1",
        "SQLAlchemy>=1.1.11",
        "Flask-SQLAlchemy>=2.3.2",
        "Schemalite>=0.1.23"
    ],
    license='MIT',
    url='https://github.com/inkmonk/flask-sqlalchemy-booster',
    author='SuryaSankar',
    author_email='suryashankar.m@gmail.com')
