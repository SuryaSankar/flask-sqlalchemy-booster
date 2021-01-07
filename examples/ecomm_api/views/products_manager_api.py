from flask import Blueprint
from flask_sqlalchemy_booster import (
    EntitiesGroup, Entity, Get, Index, Delete, Post, Put, Patch, BatchSave)
from ..models import Product, ProductPriceSlab, User, Order, OrderItem, PaymentAttempt

products_manager_api_bp = Blueprint('products_manager_api_bp', __name__)

products_manager_api_entities = EntitiesGroup(
    app_or_bp=products_manager_api_bp,
    permitted_operations=[Get, Index, Delete, Post, Put, Patch, BatchSave],
    entities=[
        Entity('products', Product,
                enable_caching=True, cache_timeout=3600),
        Entity('product-price-slabs', ProductPriceSlab),
        Entity('users', User)
    ]
)