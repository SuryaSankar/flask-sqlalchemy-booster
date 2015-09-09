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
    version='0.1.6',
    long_description='A wrapper around Flask-SQLAlchemy',
    packages=['flask_sqlalchemy_booster'],
    include_package_data=True,
    install_requires=[
        "toolspy>=0.1.",
        "Flask>=0.10.1",
        "SQLAlchemy>=0.9.8",
        "Flask-SQLAlchemy>=2.0"
        ],
    license='MIT',
    url='https://github.com/inkmonk/flask-sqlalchemy-booster',
    author='SuryaSankar',
    author_email='suryashankar.m@gmail.com')
