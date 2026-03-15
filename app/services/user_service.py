from sqlalchemy import func, literal
from app.extensions import db
from app.models import User, Orders, Address

def format_address_expr():
    """Return an SQL expression for full address, depending on DB engine."""
    if db.engine.name == 'sqlite':
        # SQLite: simple string concatenation
        return (
            func.coalesce(Address.street, '') + literal(', ') +
            func.coalesce(Address.city, '') + literal(', ') +
            func.coalesce(Address.postcode, '')
        ).label('address')
    else:
        # MySQL/Postgres: use concat_ws
        return func.concat_ws(', ', Address.street, Address.city, Address.postcode).label('address')


def get_admin_user_data():
    """Return list of users with total orders and address info."""
    total_orders = func.coalesce(func.sum(Orders.total_amount), 0).label('total_orders')
    address_expr = format_address_expr()

    query = (
        db.session.query(
            User.name,
            User.email,
            address_expr,
            total_orders
        )
        .outerjoin(Orders, User.id == Orders.user_id)
        .outerjoin(Address, (User.id == Address.user_id) & Address.current_address)
        .group_by(User.id, Address.street, Address.city, Address.postcode)
        .order_by(total_orders.desc())
    )
    return query.all()