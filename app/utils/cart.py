from flask import g, session
from sqlalchemy.orm import joinedload
from datetime import datetime, timezone
from app.models import Cart, Box, CartItem
from app.extensions import db, safe_commit


def get_user_cart_cached(user_id):
    """Fetch the cart from DB and cache it in `g`."""
    if not hasattr(g, 'cart'):
        g.cart = Cart.query.options(joinedload(Cart.items)).filter_by(user_id=user_id).first()
    return g.cart


def merge_session_basket_to_cart(user):
    """Merge session['basket'] into the DB cart for this user."""
    basket = session.get('basket', [])
    if not basket:
        return  # nothing to merge

    cart = get_user_cart_cached(user.id)
    if not cart:
        cart = Cart(user_id=user.id, created_at=datetime.now(timezone.utc))
        db.session.add(cart)
        safe_commit()

    for b in basket:
        box = Box.query.get(b.get('box_id'))
        if not box:
            continue

        existing_item = CartItem.query.filter_by(cart_id=cart.id, box_id=box.id).first()
        if existing_item:
            new_qty = existing_item.quantity + b['quantity']
            existing_item.quantity = min(new_qty, box.quantity)
        else:
            new_item = CartItem(
                cart_id=cart.id,
                box_id=box.id,
                product_id=box.product_id,
                shipment_id=box.shipment_id,
                quantity=b['quantity'],
                price=box.price_inr_unit
            )
            db.session.add(new_item)

    safe_commit()
    session.pop('basket', None)
