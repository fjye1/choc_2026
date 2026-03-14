from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, AnonymousUserMixin, login_required
from datetime import date, timedelta, timezone, datetime
from sqlalchemy import literal
from ..services import product_service
# Models
from app.models import Product, Box, Shipment, Comment, PriceAlert, OrderItem, Orders

# Services / Utils
from app.services.product_service import ProductService
from app.utils.functions import precompute_products

# Forms
from app.forms import CommentForm, AddToCartForm

# Extensions
from app.extensions import db, safe_commit

product_bp = Blueprint("product", __name__, url_prefix="/products")


@product_bp.route("/product-test")
def product_test():
    return render_template("product/product_test.html")


@product_bp.route("/search")
def search():
    query = request.args.get("q", "").strip()[:100]

    if not query:
        flash("Please enter a search term.", "warning")
        return redirect(url_for("home.index"))

    results = Product.query.filter(
        Product.name.ilike(f"%{query}%")
    ).all()

    return render_template(
        "product/search_results.html",
        query=query,
        results=results
    )

@product_bp.route("/product/<slug>", methods=["GET", "POST"])
def product_view(slug):
    product = ProductService.get_product_by_slug(slug)
    product_id = product.id

    # Similar products using embedding
    results = (
        db.session.query(Product)
        .filter(Product.is_active)
        .order_by(Product.embedding.cosine_distance(literal(product.embedding)))
        .limit(4)
        .all()
    )
    similar_products = precompute_products(results[1:4])

    # Comment form
    comment_form = CommentForm()

    # Boxes that have arrived and are in stock
    boxes = Box.query.join(Box.shipment)\
        .filter(Box.product_id == product.id, Shipment.has_arrived, Box.quantity > 0)\
        .order_by(Box.price_inr_unit.desc())\
        .all()

    # Group by price
    price_groups = {}
    for box in boxes:
        if box.price_inr_unit not in price_groups:
            price_groups[box.price_inr_unit] = {
                'quantity': 0,
                'expiry': box.expiration_date,
                'box': box,
                'shipment': box.shipment
            }
        price_groups[box.price_inr_unit]['quantity'] += box.quantity

    next_box = min(boxes, key=lambda b: b.price_inr_unit, default=None)

    add_to_cart_form = AddToCartForm(
        product_id=product.id,
        box_id=next_box.id if next_box else None,
        shipment_id=next_box.shipment_id if next_box else None
    )

    # User-specific logic
    if isinstance(current_user, AnonymousUserMixin):
        user_alert = None
        can_comment = False
    else:
        user_alert = PriceAlert.query.filter_by(user_id=current_user.id, product_id=product.id).first()
        has_purchased = db.session.query(OrderItem).join(Orders)\
            .filter(Orders.user_id == current_user.id, OrderItem.product_id == product_id).first() is not None
        already_commented = Comment.query.filter_by(user_id=current_user.id, product_id=product_id).first() is not None
        can_comment = has_purchased and not already_commented

    if comment_form.validate_on_submit() and can_comment:
        new_comment = Comment(
            user_id=current_user.id,
            product_id=product_id,
            comment=comment_form.comment_text.data,
            rating=comment_form.rating.data
        )
        db.session.add(new_comment)
        safe_commit()
        return redirect(url_for('product.product_view', slug=product.slug))

    # Recent sales for charts
    start_date = date.today() - timedelta(days=28)
    recent_sales = [s for box in product.boxes for s in box.sales_history if s.date >= start_date]
    recent_sales.sort(key=lambda s: s.date)

    dates = [s.date.strftime('%Y-%m-%d') for s in recent_sales]
    prices = [s.sold_price for s in recent_sales]
    sales = [s.sold_quantity for s in recent_sales]

    return render_template("product/product_view.html",
                           product=product,
                           form=comment_form,
                           add_to_cart_form=add_to_cart_form,
                           can_comment=can_comment,
                           dates=dates,
                           prices=prices,
                           sales=sales,
                           user_alert=user_alert,
                           similar_products=similar_products,
                           price_groups=price_groups,
                           next_box=next_box
                           )

@product_bp.route('/price-alert', methods=['POST'])
@login_required
def set_price_alert():
    # 1️⃣ Get form data
    product_id = request.form.get('product_id')
    target_price_raw = request.form.get('target_price', '').strip()

    # 2️⃣ Load product via service (safe)
    try:
        product = ProductService.get_product_by_id(product_id)
    except:
        flash("Product not found.", "warning")
        return redirect(url_for('home.index'))

    # 3️⃣ Validate target price
    try:
        target_price = float(target_price_raw)
    except ValueError:
        flash("Please enter a valid target price.", "warning")
        return redirect(url_for('product.product_view', slug=product.slug))

    # 4️⃣ Find lowest floor price among boxes
    lowest_box = (
        Box.query
        .filter_by(product_id=product.id)
        .order_by(Box.floor_price_inr_unit.asc())
        .first()
    )

    if not lowest_box:
        flash("No boxes found for this product.", "warning")
        return redirect(url_for('product.product_view', slug=product.slug))

    # 5️⃣ Check target price against floor price
    if target_price < lowest_box.floor_price_inr_unit:
        flash(
            f"Please enter a price above ₹{lowest_box.floor_price_inr_unit:.2f}",
            "warning"
        )
        return redirect(url_for('product.product_view', slug=product.slug))

    # 6️⃣ Create alert
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    alert = PriceAlert(
        user_id=current_user.id,
        product_id=product.id,
        target_price=target_price,
        expires_at=expires_at
    )
    db.session.add(alert)
    safe_commit()

    # 7️⃣ Flash success
    flash(
        f"We'll email you when {product.name} drops to ₹{target_price:.2f}! "
        "You can manage alerts in your profile.",
        "success"
    )

    # ✅ Redirect to slug-based URL
    return redirect(url_for('product.product_view', slug=product.slug))