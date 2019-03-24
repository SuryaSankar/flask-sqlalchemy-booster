
from setuptools import setup

setup(
    name='Flask-SQLAlchemy-Booster',
    version='0.5.18',
    description='A booster package for flask and sqlalchemy',
    long_description='Allows querying on Model classes, supports several common query operations, allows JSONification of models and relations and provides a simple query language for dynamically fetching data',
    packages=['flask_sqlalchemy_booster'],
    include_package_data=True,
    install_requires=[
        "toolspy>=0.2.30",
        "Flask>=0.10.1",
        "SQLAlchemy>=1.1.11",
        "Flask-SQLAlchemy>=2.3.2",
        "Schemalite>=0.1.23"
    ],
    tests_require=[
        "pytest",
        "pytest-xprocess"
    ],
    license='MIT',
    url='https://github.com/inkmonk/flask-sqlalchemy-booster',
    author='SuryaSankar',
    author_email='suryashankar.m@gmail.com')
