from app.utils.cart import get_user_cart_cached
from flask import session
from app.models import Product, Box

def build_cart_items(cart=None, session_basket=None, use_live_price=True):
    """
    Returns a tuple: (items_list, total)
    - cart: Cart object for logged-in user
    - session_basket: list of dicts for guest users
    - use_live_price: if True, always use ci.box.price_inr_unit
    """
    items = []
    total = 0

    if cart:
        for ci in cart.items if cart.items else []:
            if ci.box is None:
                raise ValueError(f"CartItem {ci.id} has no associated Box!")

            price = float(ci.box.price_inr_unit) if use_live_price else float(ci.price)

            items.append({
                'product': ci.box.product,
                'box': ci.box,
                'quantity': ci.quantity,
                'price': price,
                'cart_item_id': ci.id
            })
            total += price * ci.quantity

    elif session_basket:
        for b in session_basket:
            product = Product.query.get(b['product_id'])
            box = Box.query.get(b['box_id']) if b.get('box_id') else None

            if not product or not box:
                continue

            items.append({
                'product': product,
                'box': box,
                'quantity': b['quantity'],
                'price': float(b['price']),
                'cart_item_id': None
            })
            total += b['price'] * b['quantity']

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


