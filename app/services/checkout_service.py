import json
from app.services.cart_service import serialize_cart
from app.utils.functions import SHIPPING_FEE, SHIPPING_FREE_THRESHOLD, CARD_FEE_FIXED, CARD_FEE_PERCENT


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
