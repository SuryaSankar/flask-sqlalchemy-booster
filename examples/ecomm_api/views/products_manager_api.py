from flask import Blueprint
from flask_sqlalchemy_booster import (
    EntitiesRouter, Entity, Get, Index, Delete, Post, Put, Patch, BatchSave)
from ..models import Product, ProductPriceSlab, User, Order, OrderItem, PaymentAttempt

products_manager_api_bp = Blueprint('products_manager_api_bp', __name__)

products_manager_api_entities = EntitiesRouter(
    mount_on=products_manager_api_bp,
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
            model_class=User, get=Get(), index=Index(),
            post=Post(), put=Put(), delete=Delete()),
    }
)