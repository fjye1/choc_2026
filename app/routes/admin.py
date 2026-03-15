from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app.decorators import admin_only
from app.services.product_service import get_admin_product_data
from app.services.cart_service import get_admin_cart
from datetime import date, timedelta
from app.services.order_service import get_unfulfilled_orders
from app.services.sales_service import get_sales_last_n_days
from app.services.user_service import get_admin_user_data
from app.services.shipment_service import get_all_shipments_admin, add_box_to_shipment
from app.utils.chart_utils import format_sales_for_chart
from app.forms import ShipmentSentForm, BoxForm
from app.models import Shipment, Product, Box
from app.extensions import db, safe_commit


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


@admin_bp.route("/shipments")
@login_required
@admin_only
def view_shipments():
    shipments = get_all_shipments_admin()
    return render_template("admin/view_shipments.html", shipments=shipments)


@admin_bp.route("/create-shipment", methods=["GET", "POST"])
@login_required
@admin_only
def create_shipment():
    form = ShipmentSentForm()

    if form.validate_on_submit():
        shipment = Shipment(
            transit_cost=form.transit_cost.data
        )

        db.session.add(shipment)
        safe_commit()

        flash("Shipment created — now add boxes!", "success")
        return redirect(url_for("admin.add_box_to_shipment_route", shipment_id=shipment.id))

    return render_template("admin/create_shipment.html", form=form)



@admin_bp.route("/shipment/<int:shipment_id>/add-box", methods=["GET", "POST"])
@login_required
@admin_only
def add_box_to_shipment_route(shipment_id):
    shipment = Shipment.query.get_or_404(shipment_id)
    form = BoxForm()

    # Prepare dropdown choices
    products = Product.query.all()
    form.product_id.choices = [(p.id, p.name) for p in products]

    if form.validate_on_submit():
        box = add_box_to_shipment(
            shipment_id=shipment.id,
            product_id=form.product_id.data,
            quantity=form.quantity.data,
            landing_price_gbp_box=form.uk_price_at_shipment.data,
            weight_per_unit=next((p.weight_per_unit for p in products if p.id == form.product_id.data), 0),
            expiration_date=form.expiration_date.data,
            dynamic_pricing_enabled=form.dynamic_pricing_enabled.data
        )

        if not box:
            flash("Selected product does not exist.", "danger")
        else:
            flash("Box added to shipment!", "success")

        return redirect(url_for("admin.add_box_to_shipment_route", shipment_id=shipment.id))

    # Load existing boxes
    boxes = Box.query.filter_by(shipment_id=shipment.id).all()
    return render_template("admin/add_box_to_shipment.html", form=form, shipment=shipment, boxes=boxes)


@admin_bp.route("/delete-box/<int:box_id>", methods=["POST"])
@login_required
@admin_only
def delete_box(box_id):
    box = Box.query.get_or_404(box_id)
    shipment_id = box.shipment_id
    db.session.delete(box)
    db.session.commit()
    flash("Box deleted.", "success")
    return redirect(url_for("admin.add_box_to_shipment_route", shipment_id=shipment_id))


@admin_bp.route("/delete-shipment/<int:shipment_id>", methods=["POST"])
@login_required
@admin_only
def delete_shipment(shipment_id):
    shipment = Shipment.query.get_or_404(shipment_id)
    db.session.delete(shipment)
    db.session.commit()
    flash("Shipment and all its boxes have been deleted.", "success")
    return redirect(url_for("admin.view_shipments"))  # redirect to a shipment overview page

# @main_bp.route("/cart", methods=["GET", "POST"])
# def user_cart():
#     items, total = get_user_cart(current_user if current_user.is_authenticated else None)
#     return render_template("cart.html", items=items, total=total)