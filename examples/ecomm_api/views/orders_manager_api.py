from flask import Blueprint
from flask_sqlalchemy_booster import (
    EntitiesGroup, Entity, Get, Index, Delete, Post, Put, Patch, BatchSave)
from ..models import Product, ProductPriceSlab, User, Order, OrderItem, PaymentAttempt

orders_manager_api_bp = Blueprint('orders_manager_api_bp', __name__)

orders_manager_api_entities = EntitiesGroup(
    app_or_bp=orders_manager_api_bp,
    entities=[
        Entity('products', Product,
                enable_caching=True, cache_timeout=3600),
        Entity('product-price-slabs', ProductPriceSlab),
        Entity('users', User),
        Entity('orders', Order),
        Entity('order-items', OrderItem)
    ]
)