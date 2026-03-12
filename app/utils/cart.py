from flask import g
from sqlalchemy.orm import joinedload
from app.models import Cart

def get_user_cart_cached(user_id):
    if not hasattr(g, 'cart'):
        g.cart = Cart.query.options(joinedload(Cart.items)).filter_by(user_id=user_id).first()
    return g.cart