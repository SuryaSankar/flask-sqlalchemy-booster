from flask_sqlalchemy_booster import FlaskSQLAlchemyBooster
from sqlalchemy import func
from sqlalchemy.ext.associationproxy import association_proxy

db = FlaskSQLAlchemyBooster()

class IdTimestampMixin():
    id = db.Column(db.Integer, primary_key=True, unique=True)
    created_on = db.Column(db.DateTime(), default=func.now())  

class Product(db.Model, IdTimestampMixin):
    name = db.Column(db.String(50))
    sales_tax_percentage = db.Column(db.Numeric(precision=8, scale=2))

class ProductPriceSlab(db.Model, IdTimestampMixin):
    __mapper_args__ = {
        'polymorphic_on': 'slab_type',
        'polymorphic_identity': '__base__'
    }
    slab_type = db.Column(db.String(50))
    unit_price = db.Column(db.Numeric(precision=8, scale=2))

class ProductPriceDiscreteQtySlab(ProductPriceSlab):
    __mapper_args__ = {
        'polymorphic_identity': 'discrete_qty'
    }
    quantity = db.Column(db.Integer)

class ProductPriceRangeQtySlab(ProductPriceSlab):
    __mapper_args__ = {
        'polymorphic_identity': 'range_qty'
    }
    starts_from = db.Column(db.Integer)
    ends_at = db.Column(db.Integer)

class User(db.Model, IdTimestampMixin):
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))
    phone = db.Column(db.String(20))

class Order(db.Model, IdTimestampMixin):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_confirmed = db.Column(db.Boolean, default=False)

    user = db.relationship("User", backref=db.backref("orders"))
    user_name = association_proxy("user", "name")

class OrderItem(db.Model, IdTimestampMixin):
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    product_id =  db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer)
    unit_price = db.Column(db.Numeric(precision=8, scale=2))
    sales_tax_percentage = db.Column(db.Numeric(precision=8, scale=2))
    delivery_charges = db.Column(db.Numeric(precision=8, scale=2))

class PaymentAttempt(db.Model, IdTimestampMixin):
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    is_success = db.Column(db.Boolean, default=False)