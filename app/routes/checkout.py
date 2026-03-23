from flask import Blueprint, render_template, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
import stripe
from app.services.cart_service import get_cart_for_user
from app.utils.cart import get_user_cart_cached
from app.services.checkout_service import calculate_order_totals, get_payment_amount, format_cart_for_json, build_payment_metadata

checkout_bp = Blueprint("checkout", __name__, url_prefix="/checkout")


@checkout_bp.route('/', methods=['POST', 'GET'])
@login_required
def checkout():
    cart = get_user_cart_cached(current_user.id)

    if not cart or not cart.items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for('home.index'))

    # Soft stock check against box quantity
    for item in cart.items:
        if not item.box:
            flash(f"Box for '{item.box.name}' no longer exists.", "danger")
            return redirect(url_for('cart'))
        if item.quantity > item.box.quantity:
            flash(f"Not enough stock for '{item.box.name}' (Box: {item.box.name}). Only {item.box.quantity} left.",
                  "danger")
            return redirect(url_for('cart'))

    # Calculate total based on CartItem price (box-specific)
    totals = calculate_order_totals(cart.items)
    return render_template('checkout/checkout.html', totals=totals)


@checkout_bp.route('/cart-data')
@login_required
def cart_data():
    cart = get_user_cart_cached(current_user.id)
    data = format_cart_for_json(cart)

    print('Cart Data:', data)
    return jsonify(data)


@checkout_bp.route('/create-payment-intent', methods=['POST'])
@login_required
def create_payment_intent():
    cart = get_cart_for_user(current_user.id)
    if not cart or not cart.items:
        return jsonify({'error': 'Cart is empty'}), 400

    amount = get_payment_amount(cart)
    intent = stripe.PaymentIntent.create(
        amount=amount,
        currency='inr',
        metadata=build_payment_metadata(current_user.id, cart),
        automatic_payment_methods={'enabled': True}
    )

    return jsonify({'clientSecret': intent.client_secret})