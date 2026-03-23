from app.models import Orders
from app.services.checkout_service import process_paid_order


def get_unfulfilled_orders():
    """Returns orders with no tracking number."""
    return Orders.query.filter(Orders.tracking_number.is_(None)).all()


def get_or_create_order(payment_intent_id: str, user_id: int):
    """
    Try to get an existing order by payment_intent_id.
    If not found, process the paid order.
    Returns (order, message, is_new)
    """
    order = Orders.query.filter_by(
        payment_intent_id=payment_intent_id,
        user_id=user_id
    ).first()

    if order:
        return order, "Order confirmed!", False

    # No existing order, create it
    order, error = process_paid_order(payment_intent_id, user_id)
    if error:
        return None, error, True

    return order, "Payment successful! Order placed.", True