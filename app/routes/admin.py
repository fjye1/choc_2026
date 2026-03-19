from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app.decorators import admin_only
from app.services.product_service import get_admin_product_data
from app.services.cart_service import get_admin_cart
from datetime import date, timedelta
from app.services.product_service import ProductService
from app.services.order_service import get_unfulfilled_orders
from app.services.sales_service import get_sales_last_n_days
from app.services.user_service import get_admin_user_data
from app.services.shipment_service import get_all_shipments_admin, add_box_to_shipment
from app.utils.chart_utils import format_sales_for_chart
from app.utils.images import save_product_image
from app.forms import ShipmentSentForm, BoxForm, ProductForm
from app.models import Shipment, Product, Box, Orders
from app.extensions import db, safe_commit
from slugify import slugify
import json

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
def view_product():
    products = get_admin_product_data(days_back=28)
    return render_template(
        "admin/view_product.html",
        products=products,
        date=date,
        timedelta=timedelta
    )


@admin_bp.route("/users")
@login_required
@admin_only
def admin_users():
    results = get_admin_user_data()
    return render_template("admin/users.html", results=results)


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


@admin_bp.route('/delete-product/<int:product_id>', methods=['POST'])
@login_required
@admin_only
def delete_product(product_id):
    product = ProductService.get_product_by_id(product_id)
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for('admin.view_products'))

    if product.order_items:
        # Soft delete if product has been sold
        product.is_active = False
        safe_commit()
        flash(f"Product '{product.name}' has orders; soft deleted (hidden).", "warning")
    else:
        # Hard delete if no orders
        db.session.delete(product)
        safe_commit()
        flash(f"Product '{product.name}' was permanently deleted.", "success")

    return redirect(url_for('admin.view_products'))


@admin_bp.route('/create-product', methods=['GET', 'POST'])
@login_required
@admin_only
def create_product():
    form = ProductForm()
    if form.validate_on_submit():
        rel_image, rel_pdf_image = save_product_image(form.image.data)

        new_product = Product(
            name=form.name.data,
            description=form.description.data,
            weight_per_unit=float(form.weight_per_unit.data),
            image=rel_image,
            pdf_image=rel_pdf_image,
            ingredients=form.ingredients.data,
            allergens=json.dumps([a.strip() for a in (form.allergens.data or "").split(',') if a.strip()]),
            energy_kj=form.energy_kj.data,
            energy_kcal=form.energy_kcal.data,
            fat_g=form.fat_g.data,
            saturates_g=form.saturates_g.data,
            carbs_g=form.carbs_g.data,
            sugars_g=form.sugars_g.data,
            fibre_g=form.fibre_g.data,
            protein_g=form.protein_g.data,
            salt_g=form.salt_g.data,
            slug=slugify(form.name.data)
        )

        db.session.add(new_product)
        db.session.flush()  # get ID without commit
        new_product.slug = f"{slugify(form.name.data)}-{new_product.id}"
        safe_commit()

        flash("Product created!", "success")
        return redirect(url_for("admin.view_products"))

    return render_template('admin/create_product.html', form=form)


@admin_bp.route('/archive')
@login_required
@admin_only
def archive():
    orders = Orders.query.filter(Orders.tracking_number.isnot(None)) \
                         .order_by(Orders.created_at.desc()) \
                         .all()
    return render_template("admin/archive.html", orders=orders)

@admin_bp.route("/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
@admin_only
def edit_product(product_id):

    product = db.get_or_404(Product, product_id)
    form = ProductForm(obj=product)

    if request.method == "GET":
        form.tags.data = ", ".join(tag.name for tag in product.tags)

    if form.validate_on_submit():

        ProductService.update_product_from_form(product, form)

        safe_commit()

        return redirect(url_for("admin.view_products"))

    return render_template(
        "admin/edit_product.html",
        form=form,
        product=product
    )



@admin_bp.route("/settings")
@login_required
@admin_only
def settings():
    return render_template("admin/settings.html")


@admin_bp.route("/support")
@login_required
@admin_only
def support():
    return render_template("admin/support.html")

# @main_bp.route("/cart", methods=["GET", "POST"])
# def user_cart():
#     items, total = get_user_cart(current_user if current_user.is_authenticated else None)
#     return render_template("cart.html", items=items, total=total)