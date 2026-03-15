from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.decorators import admin_only
from app.services.product_service import get_admin_product_data
from app.services.cart_service import get_admin_cart
from datetime import date, timedelta
from app.services.order_service import get_unfulfilled_orders
from app.services.sales_service import get_sales_last_n_days
from app.services.user_service import get_admin_user_data
from app.utils.chart_utils import format_sales_for_chart


admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/test')
def admin_test():
    return render_template('admin/admin_test.html')


@admin_bp.route("/")
@login_required
@admin_only
def dashboard():
    sales_data, start_date = get_sales_last_n_days(n=28)
    day_labels, sales_values, total_sales_last_28_days = format_sales_for_chart(sales_data, start_date)
    orders = get_unfulfilled_orders()

    return render_template(
        "admin/dashboard.html",
        orders=orders,
        total=total_sales_last_28_days,
        day_labels=day_labels,
        sales_values=sales_values
    )


@admin_bp.route("/admin-cart", methods=["GET", "POST"])
@login_required
@admin_only
def admin_cart():
    items, total = get_admin_cart(current_user)
    return render_template("admin/admin_cart.html", items=items, total=total)


@admin_bp.route("/products")
@login_required
@admin_only
def admin_products():
    products = get_admin_product_data(days_back=28)
    return render_template(
        "admin/admin_products.html",
        products=products,
        date=date,
        timedelta=timedelta
    )


@admin_bp.route("/users")
@login_required
@admin_only
def admin_users():
    results = get_admin_user_data()
    return render_template("admin/admin_users.html", results=results)
