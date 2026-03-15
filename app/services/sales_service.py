from datetime import datetime, timedelta, timezone, date
from sqlalchemy import func, cast, Date
from app.extensions import db
from app.models import Orders

def get_sales_last_n_days(n=28):
    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=n-1)

    if db.engine.name == "sqlite":
        sales_data = (
            db.session.query(
                func.date(Orders.created_at).label("date"),
                func.sum(Orders.total_amount).label("sales")
            )
            .filter(func.date(Orders.created_at) >= start_date)
            .filter(func.date(Orders.created_at) <= today)
            .group_by(func.date(Orders.created_at))
            .order_by(func.date(Orders.created_at))
            .all()
        )
    else:
        sales_data = (
            db.session.query(
                cast(Orders.created_at, Date).label("date"),
                func.sum(Orders.total_amount).label("sales")
            )
            .filter(cast(Orders.created_at, Date) >= start_date)
            .filter(cast(Orders.created_at, Date) <= today)
            .group_by("date")
            .order_by("date")
            .all()
        )
    return sales_data, start_date