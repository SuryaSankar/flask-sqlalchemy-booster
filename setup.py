
from setuptools import setup

setup(
    name='Flask-SQLAlchemy-Booster',
    version='0.6.14',
    description='A booster package for Flask and SQLAlchemy',
    long_description='Allows querying on Model classes, supports several common query operations, allows JSONification of models and relations and provides a simple query language for dynamically fetching data',
    packages=['flask_sqlalchemy_booster'],
    include_package_data=True,
    install_requires=[
        "toolspy>=0.3.1",
        "Flask>=1.0.2",
        "SQLAlchemy>=1.3.1",
        "Flask-SQLAlchemy>=2.3.2",
        "Schemalite>=0.2.1",
        "bleach",
        "future"
    ],
    tests_require=[
        "pytest"
    ],
    license='MIT',
    url='https://github.com/SuryaSankar/flask-sqlalchemy-booster',
    author='SuryaSankar',
    author_email='suryashankar.m@gmail.com')
