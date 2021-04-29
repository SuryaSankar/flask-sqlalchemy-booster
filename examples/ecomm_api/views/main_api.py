from flask import Blueprint
from flask_security import current_user
from flask_sqlalchemy_booster import (
    EntitiesRouter, Entity, Get, Index, Delete, Post, Put, Patch, BatchSave)
from ..models import Product, ProductPriceSlab, User, Order, OrderItem, PaymentAttempt

main_api_bp = Blueprint('main_api_bp', __name__)

def set_current_user_id(data, resource):
    if current_user.is_authenticated:
        data['user_id'] = current_user.get_id()

main_api_entities = EntitiesRouter(
    router={
        "products": Entity(
            model_class=Product,
            query_modifier=lambda q: q.filter(Product.published == True),
            enable_caching=True, cache_timeout=3600,
            get=Get(), index=Index()),
        "product-price-slabs": Entity(
            model_class=ProductPriceSlab,
            get=Get(), index=Index()),
        "users": Entity(
            model_class=User,
            get=Get()),
        "orders": Entity(
            model_class=Order,
            query_modifier=lambda q: q.filter(
                Order.user_id == current_user.id),
            get=Get(), index=Index(),
            post=Post(before_save=[set_current_user_id]),
            put=Put()
        ),
        "order-items": Entity(
            model_class=OrderItem,
            get=Get(), index=Index(), post=Post(), put=Put(), delete=Delete()),
        "payment-attempts":  Entity(
            model_class=PaymentAttempt,
            get=Get(), index=Index(), post=Post(), put=Put())
    }
)

main_api_entities.mount_on(main_api_bp)
