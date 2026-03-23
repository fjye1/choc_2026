import json
from app.services.cart_service import serialize_cart
from app.utils.functions import SHIPPING_FEE, SHIPPING_FREE_THRESHOLD, CARD_FEE_FIXED, CARD_FEE_PERCENT
import stripe
from app.models import Cart, Address, Orders, OrderItem, Tasks
from app.extensions import safe_commit, db
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

def calculate_order_totals(cart_items):
    subtotal = 0

    for item in cart_items:
        # support dicts (JSON) and objects (DB)
        if isinstance(item, dict):
            price = float(item["price"])
            quantity = int(item["quantity"])
        else:
            price = float(item.price)
            quantity = int(item.quantity)

        subtotal += price * quantity

    shipping = 0 if subtotal >= SHIPPING_FREE_THRESHOLD else SHIPPING_FEE
    card_fee = round(CARD_FEE_FIXED + (subtotal + shipping) * (CARD_FEE_PERCENT / 100), 2)
    grand_total = round(subtotal + shipping + card_fee, 2)

    return {
        "subtotal": round(subtotal, 2),
        "shipping": shipping,
        "free_shipping": subtotal >= SHIPPING_FREE_THRESHOLD,
        "card_fee": card_fee,
        "grand_total": grand_total,
    }


def format_cart_for_json(cart):
    """Return cart as JSON-serializable dict with totals."""
    if not cart or not cart.items:
        return {'items': [], 'total': 0}

    items = [
        {
            'product_id': item.box.product_id,
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


def build_payment_metadata(user_id, cart):
    """Return metadata dict for Stripe PaymentIntent."""
    totals = calculate_order_totals(cart.items)
    return {
        'user_id': str(user_id),
        'cart': json.dumps(serialize_cart(cart)['items']),
        'subtotal': str(totals["subtotal"]),
        'shipping': str(totals["shipping"]),
        'card_fee': str(totals["card_fee"]),
        'grand_total': str(totals["grand_total"]),
        'free_shipping': str(totals["free_shipping"]),
    }


def get_payment_amount(cart):
    """Return total amount in smallest currency unit (paise) for Stripe."""
    totals = calculate_order_totals(cart.items)
    return int(round(float(totals["grand_total"]) * 100))


def process_paid_order(payment_intent_id: str, user_id: int):
    """Create an order from a Stripe PaymentIntent and the user's cart."""
    try:
        with db.session.no_autoflush:  # 👈 prevents autoflush during queries
            existing_order = Orders.query.filter_by(payment_intent_id=payment_intent_id).first()
            if existing_order:
                print(f"[Order] Already processed {payment_intent_id}, skipping")
                return existing_order, None

            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            if intent.status != "succeeded":
                return None, "Payment not completed"

            cart = Cart.query.filter_by(user_id=user_id).first()
            if not cart or not cart.items:
                return None, "Cart is empty"

            shipping_address = Address.query.filter_by(user_id=user_id, current_address=True).first()
            billing_address = Address.query.filter_by(user_id=user_id, current_address=True).first()
            if not shipping_address or not billing_address:
                return None, "Missing address info"

            order_id = f"ORD{int(datetime.now(timezone.utc).timestamp())}"
            totals = calculate_order_totals(cart.items)
            payment_method = "live" if intent.livemode else "test"

            order = Orders(
                order_id=order_id,
                user_id=user_id,
                order_date=datetime.now(timezone.utc),
                status="paid",
                subtotal=totals["subtotal"],
                shipping=totals["shipping"],
                card_fee=totals["card_fee"],
                total_amount=totals["grand_total"],
                payment_method=payment_method,
                payment_intent_id=payment_intent_id,
                shipping_address=shipping_address,
                billing_address=billing_address
            )
            db.session.add(order)

            for item in cart.items:
                order_item = OrderItem(
                    order=order,
                    product_id=item.product_id,
                    box_id=item.box_id,
                    shipment_id=item.shipment_id,
                    quantity=item.quantity,
                    price_at_purchase=float(item.price)
                )
                db.session.add(order_item)

                if item.box:
                    item.box.sold_today = (item.box.sold_today or 0) + item.quantity
                    item.box.quantity -= item.quantity
                    if item.box.quantity <= 0:
                        item.box.is_active = False

            for item in cart.items:
                db.session.delete(item)

        # Commit outside no_autoflush block
        try:
            safe_commit()
        except IntegrityError:
            db.session.rollback()
            existing_order = Orders.query.filter_by(payment_intent_id=payment_intent_id).first()
            print(f"[Order] Race condition caught for {payment_intent_id}, returning existing order")
            return existing_order, None

        try:
            new_task = Tasks(
                task_name="send_invoice",
                arg1=order.order_id,
                arg2=order.user.email
            )
            db.session.add(new_task)
            safe_commit()
        except Exception as e:
            print(f"[Invoice Queue Error]: {e}")

        return order, None

    except IntegrityError as e:  # 👈 catch race condition at outer level too
        db.session.rollback()
        existing_order = Orders.query.filter_by(payment_intent_id=payment_intent_id).first()
        print(f"[Order] Race condition caught (outer) for {payment_intent_id}")
        return existing_order, None

    except Exception as e:
        print(f"[Order Processing Error]: {e}")
        db.session.rollback()
        return None, str(e)
