from flask_sqlalchemy_booster import FlaskSQLAlchemyBooster
from sqlalchemy import func
from flask_sqlalchemy_booster import FlaskBooster
from flask_sqlalchemy_booster.crud_api_view import register_crud_routes_for_models
from sqlalchemy.ext.associationproxy import association_proxy

from werkzeug.serving import run_simple


db = FlaskSQLAlchemyBooster()


class Task(db.Model):
    _autogenerate_dict_struct_if_none_ = True

    id = db.Column(db.Integer, primary_key=True, unique=True)
    created_on = db.Column(db.DateTime(), default=func.now())
    title = db.Column(db.String(300))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    user = db.relationship("User")
    user_email = association_proxy(
        "user", "email", creator=lambda email: User.first(email=email)
    )

class User(db.Model):
    _autogenerate_dict_struct_if_none_ = True

    id = db.Column(db.Integer, primary_key=True, unique=True)
    created_on = db.Column(db.DateTime(), default=func.now())
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    gender = db.Column(db.Enum('male', 'female', 'transgender'), nullable=False)
    marital_status = db.Column(db.Enum('married', 'single'))

    @property
    def first_name(self):
        return self.name.split(" ")[0]


def create_todolist_app():
    app = FlaskBooster(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    app.config['DEBUG'] = True

    db.init_app(app)

    with app.app_context():
        db.create_all()

    print("about to call register_crud_routes_for_models")

    register_crud_routes_for_models(app, {
        Task: {
            'url_slug': 'tasks'
        },
        User: {
            'url_slug': 'users'
        }
    }, register_views_map=True, register_schema_definition=True)
    return app

def run_application(app):
    run_simple('0.0.0.0', 5000, app)


if __name__ == '__main__':
    app = create_todolist_app()

    run_application(app)
