from app.models import Orders

def get_unfulfilled_orders():
    """Returns orders with no tracking number."""
    return Orders.query.filter(Orders.tracking_number.is_(None)).all()