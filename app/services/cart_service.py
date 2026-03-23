from app.utils.cart import get_user_cart_cached
from flask_login import current_user
from flask import session
from datetime import datetime, timezone
from app.models import Cart, CartItem, Product, Box
from app.extensions import db, safe_commit


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


def add_item_to_cart(box, product_id, shipment_id, quantity):
    """
    Add an item to either DB cart (logged-in) or session basket (guest).
    Returns a tuple: (success: bool, message: str)
    """
    if quantity > box.quantity:
        return False, f"Only {box.quantity} items left in stock for this box."

    # Logged-in user
    if current_user.is_authenticated:
        cart = get_user_cart_cached(current_user.id)
        if not cart:
            cart = Cart(user_id=current_user.id, created_at=datetime.now(timezone.utc))
            db.session.add(cart)
            safe_commit()

        cart_item = CartItem.query.filter_by(cart_id=cart.id, box_id=box.id).first()

        if cart_item:
            new_qty = cart_item.quantity + quantity
            if new_qty > box.quantity:
                return False, f"Only {box.quantity - cart_item.quantity} items left in stock."
            cart_item.quantity = new_qty
        else:
            cart_item = CartItem(
                cart_id=cart.id,
                box_id=box.id,
                product_id=box.product_id,
                shipment_id=box.shipment_id,
                quantity=quantity,
                price=box.price_inr_unit
            )
            db.session.add(cart_item)

        safe_commit()
        return True, f"Added {quantity} of '{box.product.name}' to your cart."

    # Guest user (session-based)
    else:
        basket = session.get('basket', [])
        found = False
        for item in basket:
            if item['box_id'] == box.id:
                new_qty = item['quantity'] + quantity
                if new_qty > box.quantity:
                    return False, f"Only {box.quantity - item['quantity']} items left in stock."
                item['quantity'] = new_qty
                found = True
                break

        if not found:
            basket.append({
                'product_id': product_id,
                'box_id': box.id,
                'shipment_id': shipment_id,
                'quantity': quantity,
                'price': float(box.price_inr_unit)
            })

        session['basket'] = basket
        return True, f"Added {quantity} of '{box.product.name}' to your cart."


def remove_item_from_cart(item_id, user_id):
    """
    Remove a CartItem from a user's cart safely.
    """
    item = CartItem.query.get(item_id)
    if not item:
        raise ValueError("Cart item not found.")
    if item.cart.user_id != user_id:
        raise ValueError("Unauthorized action.")

    # Access name first
    product_name = item.box.product.name if item.box else "Unknown Product"

    db.session.delete(item)
    safe_commit()

    return f"Item '{product_name}' removed from cart."


def get_cart_for_user(user_id):
    """Fetch the cart for a user. Returns None if empty."""
    return get_user_cart_cached(user_id)


def serialize_cart(cart):
    """Convert a cart into JSON-serializable format for Stripe or frontend."""
    if not cart or not cart.items:
        return {'items': [], 'total': 0}

    items = [
        {
            'product_id': item.box.product_id if item.box else None,
            'box_id': item.box_id,
            'shipment_id': item.shipment_id,
            'product_name': item.box.product.name if item.box else None,
            'quantity': item.quantity,
            'price': float(item.price),
            'expiration_date': item.box.expiration_date.strftime('%Y-%m-%d') if item.box else None
        }
        for item in cart.items
    ]
    total = sum(item['price'] * item['quantity'] for item in items)
    return {'items': items, 'total': total}