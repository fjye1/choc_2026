from flask import Blueprint, session, abort, render_template
from flask_login import current_user, login_required
from app.utils.cart import get_user_cart_cached
from app.services.cart_service import build_cart_items
from app.decorators import admin_only

cart_bp = Blueprint("cart", __name__, url_prefix="/cart")


@cart_bp.route('/view_cart')
def view_cart():
    if current_user.is_authenticated:
        cart = get_user_cart_cached(current_user.id)
        items, total = build_cart_items(cart=cart, use_live_price=True)
    else:
        basket = session.get('basket', [])
        items, total = build_cart_items(session_basket=basket)

    return render_template('cart/cart.html', items=items, total=total)


@cart_bp.route('/admin/admin_cart', methods=['GET', 'POST'])
@login_required
@admin_only
def admin_cart():
    if current_user.is_authenticated:
        cart = get_user_cart_cached(current_user.id)
        items, total = build_cart_items(cart=cart, use_live_price=True)
    else:
        basket = session.get('basket', [])
        items, total = build_cart_items(session_basket=basket)

    return render_template("admin/admin_cart.html", items=items, total=total)