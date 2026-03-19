from datetime import date, datetime, timedelta, timezone
from sqlalchemy import func
from sqlalchemy.orm import joinedload, subqueryload
from app.extensions import db
from app.models import Product, PriceAlert, Box, Tag
from app.utils.images import save_product_image

class ProductService:
    @staticmethod
    def get_product_by_slug(slug):
        return Product.query.filter_by(slug=slug).first_or_404()

    """
    Service layer that abstracts Product data access.
    Routes talk to this service, not directly to the model.
    """

    @staticmethod
    def get_product_by_id(product_id):
        """Get a product with all its data (including dynamic pricing info)"""
        product = Product.query.get_or_404(product_id)
        # Right now, everything is in Product model
        # Later, you can fetch from DynamicPricing table here
        return product

    @staticmethod
    def get_product_detail(product_id):
        """
        Get product details as a dictionary.
        This completely hides the underlying structure.
        """
        product = Product.query.get_or_404(product_id)

        # Return a clean data structure
        return {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'description': product.description,
            'image': product.image,
            'weight': product.weight,
            'quantity': product.quantity,
            'is_active': product.is_active,
            'average_rating': product.average_rating(),
            # Dynamic pricing info
            'dynamic_pricing': {
                'enabled': product.dynamic_pricing_enabled,
                'expiration_date': product.expiration_date,
                'pending_price': product.pending_price,
                'target_daily_sales': product.target_daily_sales,
                'sold_today': product.sold_today,
                'last_price_update': product.last_price_update,
                'floor_price': product.floor_price
            }
        }

    @staticmethod
    def update_product_from_form(product, form):
        """Update product fields from admin form."""

        product.name = form.name.data
        product.description = form.description.data

        # Image upload
        ProductService._handle_image_upload(product, form.image.data)

        # Tags
        ProductService._update_tags(product, form.tags.data)

    @staticmethod
    def _handle_image_upload(product, image_file):
        """Handles optional image upload"""

        if not image_file or not getattr(image_file, "filename", None):
            return

        rel_image, rel_pdf = save_product_image(image_file)

        if rel_image:
            product.image = rel_image
        if rel_pdf:
            product.pdf_image = rel_pdf

    @staticmethod
    def _update_tags(product, tag_string):

        tag_names = [n.strip() for n in tag_string.split(",") if n.strip()]
        tag_objects = []

        for name in tag_names:
            tag = Tag.query.filter_by(name=name).first()

            if not tag:
                tag = Tag(name=name)
                db.session.add(tag)

            tag_objects.append(tag)

        product.tags = tag_objects


def get_admin_product_data(days_back=28):
    """Returns a list of products with aggregated data for admin dashboard"""
    now = datetime.now(timezone.utc)
    start_date = date.today() - timedelta(days=days_back)

    products = Product.query.options(joinedload(Product.boxes).joinedload(Box.sales_history)).all()

    for product in products:
        active_boxes = [b for b in product.boxes if b.is_active]
        product.has_active_boxes = bool(active_boxes)

        # total quantity
        total_quantity = sum(b.quantity for b in active_boxes)
        product.total_quantity = total_quantity

        # average unit price
        product.avg_price = (
                sum(b.price_inr_unit * b.quantity for b in active_boxes) / total_quantity
        ) if total_quantity else 0

        # earliest expiration
        earliest_box = min(
            (b for b in active_boxes if b.expiration_date),
            key=lambda b: b.expiration_date,
            default=None
        )
        product.earliest_expiry = earliest_box.expiration_date if earliest_box else None
        product.days_left = (earliest_box.expiration_date - date.today()).days if earliest_box else None

        # default expiration for boxes without one
        for box in active_boxes:
            if not box.expiration_date:
                box.expiration_date = date.today() + timedelta(days=30)
            box.days_left = (box.expiration_date - date.today()).days

        # dynamic pricing
        product.dynamic_pricing_enabled = any(b.dynamic_pricing_enabled for b in active_boxes)

        # tag names
        product.tag_names = ', '.join([t.name for t in product.tags])

        # recent sales
        recent_sales = [s for b in active_boxes for s in b.sales_history if s.date >= start_date]
        product.recent_sales = sorted(recent_sales, key=lambda s: s.date)

        # revenue, cost, profit
        product.total_revenue = sum(s.sold_quantity * s.sold_price for s in recent_sales)
        product.total_cost = sum(s.sold_quantity * (s.floor_price or 0) for s in recent_sales)
        product.profit = product.total_revenue - product.total_cost
        product.profit_percent = (product.profit / product.total_revenue * 100) if product.total_revenue else 0

        # average alert price
        avg_alert_price = (
            db.session.query(func.avg(PriceAlert.target_price))
            .filter(
                PriceAlert.product_id == product.id,
                PriceAlert.expires_at > now
            ).scalar()
        )
        product.avg_alert_price = round(avg_alert_price or 0, 2)

    # sort by profit percentage descending
    products.sort(key=lambda p: p.profit_percent, reverse=True)

    return products
