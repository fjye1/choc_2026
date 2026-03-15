from app.utils.cart import get_user_cart_cached
from flask import session
from app.models import Product

def build_cart_items(cart=None, session_basket=None):
    """
    Returns: (items_list, total_cost)
    Handles both DB carts and session baskets.
    """
    items = []
    total = 0

    if cart:
        for ci in cart.items if cart.items else []:
            items.append({
                "product": ci.box.product,
                "quantity": ci.quantity,
                "price": ci.box.price_inr_unit,
                "cart_item_id": ci.id
            })
            total += ci.box.price_inr_unit * ci.quantity

    elif session_basket:
        for b in session_basket:
            product = Product.query.get(b["product_id"])
            if not product:
                continue
            items.append({
                "product": product,
                "quantity": b["quantity"],
                "price": b["price"],
                "cart_item_id": None
            })
            total += b["price"] * b["quantity"]

    return items, total


def get_admin_cart(user):
    """
    Admin cart: uses DB cart for current_user.
    """
    cart = get_user_cart_cached(user.id)
    return build_cart_items(cart=cart)


def get_user_cart(user=None):
    """
    Normal user cart: tries DB cart first, then session basket.
    """
    cart = get_user_cart_cached(user.id) if user and user.is_authenticated else None
    session_basket = None if cart else session.get("basket", [])
    return build_cart_items(cart=cart, session_basket=session_basket)