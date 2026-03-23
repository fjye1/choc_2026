from flask import Blueprint, render_template, flash, redirect, url_for, jsonify, request, current_app
from flask_login import login_required, current_user
import stripe
from app.services.cart_service import get_cart_for_user
from app.utils.cart import get_user_cart_cached
from app.services.checkout_service import calculate_order_totals, get_payment_amount, format_cart_for_json, \
    build_payment_metadata, process_paid_order
from app.services.order_service import get_or_create_order
from config import Config


stripe.api_key = Config.STRIPE_API_KEY

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

    # get total amount to charge (in paise)
    amount = get_payment_amount(cart)
    if not amount or amount <= 0:
        return jsonify({'error': 'Invalid payment amount'}), 400

    try:
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='inr',
            metadata=build_payment_metadata(current_user.id, cart),
            automatic_payment_methods={'enabled': True}
        )
    except stripe.error.StripeError as e:
        print("Stripe error:", e.user_message or str(e))
        return jsonify({'error': e.user_message or "Stripe error"}), 400
    except Exception as e:
        print("Server error:", str(e))
        return jsonify({'error': "Server error creating PaymentIntent"}), 500

    # success
    return jsonify({'clientSecret': intent.client_secret})

@checkout_bp.route('/success')
@login_required
def payment_success():
    payment_intent_id = request.args.get("payment_intent")
    if not payment_intent_id:
        flash("Payment info missing.", "danger")
        return redirect(url_for('home.index'))

    order, message, _ = get_or_create_order(payment_intent_id, current_user.id)
    if not order:
        flash(message, "danger")
        return redirect(url_for('payment_failure'))

    flash(message, "success")
    return render_template('checkout/payment_success.html', order=order)

@checkout_bp.route('/failure')
def payment_failure():
    return render_template('checkout/payment_failure.html')

@checkout_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = current_app.config.get("ENDPOINT_SECRET")

    # Verify webhook signature
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        print("[Webhook] Invalid payload")
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        print("[Webhook] Invalid signature")
        return 'Invalid signature', 400

    # Handle payment success
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        payment_intent_id = payment_intent['id']
        user_id = payment_intent.get('metadata', {}).get('user_id')

        if not user_id:
            print(f"[Webhook] Missing user_id for payment_intent {payment_intent_id}")
            return 'Missing user_id', 400

        print(f"[Webhook] Processing order for payment_intent {payment_intent_id}, user {user_id}")

        order, error = process_paid_order(payment_intent_id, int(user_id))

        if error:
            print(f"[Webhook] Error processing order: {error}")
            # Return 200 anyway—Stripe will retry automatically
        else:
            print(f"[Webhook] Order {order.order_id} created successfully")

    return 'Success', 200