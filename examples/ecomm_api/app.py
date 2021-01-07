from flask_sqlalchemy_booster import FlaskBooster
from .views import main_api_bp, orders_manager_api_bp, products_manager_api_bp

from werkzeug.serving import run_simple


def create_ecomm_app():
    app = FlaskBooster(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    app.config['DEBUG'] = True
    db.init_app(app)

    with app.app_context():
        db.create_all()
    
    app.register_blueprint(main_api_bp, url_prefix='/api')
    app.register_blueprint(orders_manager_api_bp, url_prefix='/orders-manager-api')
    app.register_blueprint(products_manager_api_bp, url_prefix='/products-manager-api')
    return app

def run_application(app):
    run_simple('0.0.0.0', 5000, app)


if __name__ == '__main__':
    app = create_ecomm_app()

    run_application(app)
