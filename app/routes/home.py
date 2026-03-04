from flask import Blueprint, render_template, session, flash, request
from flask_login import current_user
from sqlalchemy import func

from app.extensions import db
from app.models import Product, Box, Comment, PriceAlert, Tag
from app.utils.functions import precompute_products  # assuming this exists

home_bp = Blueprint('home', __name__)


@home_bp.route("/")
def index():
    # Banner
    if not session.get("portfolio_banner_shown"):
        flash("""
            <b>⚠️ Site Under Construction</b><br>
            Please do not use real payment details.<br>
            Payments run in <b>Stripe test mode</b> only.
            <ul style="margin:6px 0 0 18px">
              <li>Visa: 4242 4242 4242 4242 (any future expiry, CVC, postcode)</li>
              <li>3D Secure test: 4000 0027 6000 3184</li>
            </ul>
            <b>No orders will be fulfilled.</b><br><br>
            <b>Features you can try:</b>
            <ul style="margin:6px 0 0 18px">
              <li>Place orders to see live <b>order updates</b> and <b>confirmation emails</b></li>
              <li>Dynamic <b>price alerts</b> & <b>daily price updates</b></li>
            </ul>
            """, "demo")
        session["portfolio_banner_shown"] = True

    # Random comments
    random_comments = Comment.query.order_by(func.random()).limit(3).all()

    admin = current_user.admin if current_user.is_authenticated else False

    # Preload products with boxes and comments
    products = Product.query.options(
        db.joinedload(Product.boxes).joinedload(Box.shipment),
        db.selectinload(Product.comments)
    ).filter_by(is_active=True).all()

    products = precompute_products(products)
    sorted_products = sorted(products, key=lambda p: p._avg_rating, reverse=True)
    boxes = [b for p in products for b in p.boxes if b.is_active]

    # User alerts
    user_alerts = {}
    if current_user.is_authenticated:
        product_ids = [p.id for p in products]
        alerts = PriceAlert.query.filter(
            PriceAlert.user_id == current_user.id,
            PriceAlert.product_id.in_(product_ids)
        ).all()
        user_alerts = {alert.product_id: alert for alert in alerts}

    return render_template(
        "home/index.html",
        products=products,
        admin=admin,
        comments=random_comments,
        sorted_products=sorted_products,
        boxes=boxes,
        user_alerts=user_alerts
    )


@home_bp.route('/catalog')
def catalog():
    product_key = request.args.get('product')
    selected_tags = request.args.getlist('tags')
    sort = request.args.get('sort')

    query = Product.query.filter_by(is_active=True)

    if product_key:
        tag = Tag.query.filter(Tag.name.ilike(f"%{product_key}%")).first()
        if tag:
            query = tag.products.filter_by(is_active=True)
        else:
            query = Product.query.filter(False)  # No match → empty
    elif selected_tags:
        query = (
            query
            .join(Product.tags)
            .filter(Tag.name.in_(selected_tags))
            .group_by(Product.id)
        )

    products = query.options(
        db.joinedload(Product.boxes).joinedload(Box.shipment),
        db.selectinload(Product.comments)
    ).all()

    products = precompute_products(products)

    # Sorting
    if sort == 'price_asc':
        products.sort(key=lambda p: p._lowest_box.price_inr_unit if p._lowest_box else float('inf'))
    elif sort == 'price_desc':
        products.sort(key=lambda p: p._lowest_box.price_inr_unit if p._lowest_box else float('inf'), reverse=True)
    elif sort == 'rating_asc':
        products.sort(key=lambda p: p._avg_rating)
    elif sort == 'rating_desc':
        products.sort(key=lambda p: p._avg_rating, reverse=True)

    product_ids = [p.id for p in products]
    user_alerts = {}
    if current_user.is_authenticated:
        alerts = PriceAlert.query.filter(
            PriceAlert.user_id == current_user.id,
            PriceAlert.product_id.in_(product_ids)
        ).all()
        user_alerts = {alert.product_id: alert for alert in alerts}

    all_tags = (
        db.session.query(Tag, func.count(Product.id).label("tag_count"))
        .join(Product.tags)
        .group_by(Tag.id)
        .order_by(func.count(Product.id).desc())
        .limit(10)
        .all()
    )

    return render_template(
        'home/catalog.html',  # updated template path
        product_key=product_key,
        products=products,
        all_tags=all_tags,
        selected_tags=selected_tags,
        sort=sort,
        user_alerts=user_alerts
    )
