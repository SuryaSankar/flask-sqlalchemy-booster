from flask_sqlalchemy_booster import FlaskSQLAlchemyBooster
from sqlalchemy import func
from flask_sqlalchemy_booster import FlaskBooster
from flask_sqlalchemy_booster.crud_api_view import register_crud_routes_for_models

from werkzeug.serving import run_simple




db = FlaskSQLAlchemyBooster()


class Task(db.Model):
    _autogenerate_dict_struct_if_none_ = True

    id = db.Column(db.Integer, primary_key=True, unique=True)
    created_on = db.Column(db.DateTime(), default=func.now())
    title = db.Column(db.String(300))

class User(db.Model):
    _autogenerate_dict_struct_if_none_ = True

    id = db.Column(db.Integer, primary_key=True, unique=True)
    created_on = db.Column(db.DateTime(), default=func.now())
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))


def create_todolist_app():
    app = FlaskBooster(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    app.config['DEBUG'] = True

    db.init_app(app)

    with app.app_context():
        db.create_all()

    register_crud_routes_for_models(app, {
        Task: {
            'url_slug': 'tasks'
        },
        User: {
            'url_slug': 'users'
        }
    })
    return app

def run_application(app):
    run_simple('0.0.0.0', 5000, app)


if __name__ == '__main__':
    app = create_todolist_app()

    run_application(app)
