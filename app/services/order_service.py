from app.models import Orders, Tasks
from app.services.checkout_service import process_paid_order
from app.extensions import safe_commit, db

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


def add_tracking_to_order(order_id: str, tracking_code: str):
    order = db.get_or_404(Orders, order_id)

    order.tracking_number = tracking_code
    safe_commit()

    try:
        new_task = Tasks(
            task_name="send_tracking",
            arg1=order.order_id,
            arg2=order.user.email,
            arg3=order.tracking_number
        )
        db.session.add(new_task)
        safe_commit()
    except Exception as e:
        print(f"[Tracking Task Error]: {e}")

    return order