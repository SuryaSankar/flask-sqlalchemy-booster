from flask import Blueprint
from flask_sqlalchemy_booster import (
    EntitiesGroup, Entity, Get, Index, Delete, Post, Put, Patch, BatchSave)
from ..models import Product, ProductPriceSlab, User, Order, OrderItem, PaymentAttempt

main_api_bp = Blueprint('main_api_bp', __name__)

main_api_entities = EntitiesGroup(
    app_or_bp=main_api_bp,
    entities=[
        Entity('products', Product,
                enable_caching=True, cache_timeout=3600,
                permitted_operations=[Get, Index]),
        Entity('product-price-slabs', ProductPriceSlab,
                permitted_operations=[Get, Index]),
        Entity('users', User,
                permitted_operations=[Get]),
        Entity('orders', Order,
                permitted_operations=[Get, Index, Post, Put]),
        Entity('order-items', OrderItem,
                permitted_operations=[Get, Index, Post, Put, Delete]),
        Entity('payment-attempts', PaymentAttempt,
                permitted_operations=[Get, Index, Post, Put])
    ]
)



