from flask import Blueprint, session, render_template, flash, redirect, request, url_for
from flask_login import current_user, login_required
from app.utils.cart import get_user_cart_cached
from app.services.cart_service import build_cart_items, add_item_to_cart, remove_item_from_cart
from app.decorators import admin_only
from app.forms import AddToCartForm
from app.models import Box

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


@cart_bp.route('/add', methods=['POST'])
def add_to_cart():
    form = AddToCartForm()

    product_id = form.product_id.data
    box_id = form.box_id.data
    shipment_id = form.shipment_id.data
    quantity = form.quantity.data

    box = Box.query.get_or_404(box_id)

    success, message = add_item_to_cart(box, product_id, shipment_id, quantity)
    if success:
        flash(message, "success")
    else:
        flash(message, "warning")

    return redirect(request.referrer or url_for('cart.view_cart'))


@cart_bp.route('/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_cart_item(item_id):
    try:
        message = remove_item_from_cart(item_id, current_user.id)
        flash(message, "success")
    except ValueError as e:
        flash(str(e), "warning")

    return redirect(url_for('cart.view_cart'))