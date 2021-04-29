from flask import Blueprint
from flask_sqlalchemy_booster import (
    EntitiesRouter, Entity, Get, Index, Delete, Post, Put, Patch, BatchSave)
from ..models import Product, ProductPriceSlab, User, Order, OrderItem, PaymentAttempt

orders_manager_api_bp = Blueprint('orders_manager_api_bp', __name__)

orders_manager_api_entities = EntitiesRouter(
    routes={
        "products": Entity(
            model_class=Product,
            get=Get(), index=Index(), post=Post(),
            put=Put(), delete=Delete(),
            enable_caching=True, cache_timeout=3600),
        "product-price-slabs": Entity(
            model_class=ProductPriceSlab,
            get=Get(), index=Index(), post=Post(),
            put=Put(), delete=Delete()),
        "users": Entity(
            model_class=User, url_slugget=Get(), index=Index(),
            post=Post(), put=Put(), delete=Delete()),
        "orders": Entity(
            model_class=Order,
            get=Get(), index=Index(), post=Post(),
            put=Put(), delete=Delete()),
        "order-items": Entity(
            model_class=OrderItem,
            get=Get(), index=Index(), post=Post(),
            put=Put(), delete=Delete())
    },
    mount_on=orders_manager_api_bp
)