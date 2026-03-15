from flask import Blueprint, render_template
from flask import render_template
from flask_login import login_required
from sqlalchemy import func, cast, Date
from datetime import datetime, timedelta, timezone
from app.decorators import admin_only

from app.models import Orders
from app import db




admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/test')
def admin_test():
    return render_template('admin/admin_test.html')

@admin_bp.route("/")
@login_required
@admin_only
def dashboard():

    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=27)

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

    sales_dict = {d: s or 0 for d, s in sales_data}

    day_labels = [(start_date + timedelta(days=i)).strftime("%d %b") for i in range(28)]
    sales_values = [sales_dict.get(start_date + timedelta(days=i), 0) for i in range(28)]

    total_sales_last_28_days = sum(sales_values)

    orders = Orders.query.filter(Orders.tracking_number.is_(None)).all()

    return render_template(
        "admin/dashboard.html",
        orders=orders,
        total=total_sales_last_28_days,
        day_labels=day_labels,
        sales_values=sales_values
    )