from flask import g
from app.models import Product
from collections import Counter

def inject_globals():
    """
    Provides global context variables to all templates.
    """
    return {
        "current_user": getattr(g, "current_user", None),  # or current_user if using Flask-Login
        "cart_items": [],
        "admin": False

    }



def inject_dummy_products():
    """
    Provides dummy products for testing templates before database is ready.
    """
    dummy_products = [
        {
            'id': 1,
            'name': 'Dark Chocolate Delight',
            'slug': 'dark-chocolate-delight',
            'image': 'static/images/sample_product_1.png',
            '_avg_rating': 4.5,
            '_lowest_box': {'price_inr_unit': 299},
            'is_active': True
        },
        {
            'id': 2,
            'name': 'Milk Chocolate Bliss',
            'slug': 'milk-chocolate-bliss',
            'image': 'static/images/sample_product_2.png',
            '_avg_rating': 4.0,
            '_lowest_box': {'price_inr_unit': 249},
            'is_active': True
        },
        {
            'id': 3,
            'name': 'White Chocolate Dream',
            'slug': 'white-chocolate-dream',
            'image': 'static/images/sample_product_3.png',
            '_avg_rating': 4.8,
            '_lowest_box': {'price_inr_unit': 199},
            'is_active': True
        },
    ]
    return dict(dummy_products=dummy_products, user_alerts={})


def inject_top_tags():
    # Only active products
    products = Product.query.filter_by(is_active=True).all()

    # Flatten all tags
    all_tags = []
    for p in products:
        all_tags.extend({t.name for t in p.tags})  # use set to avoid duplicates per product

    # Top 6 tags overall
    top_six = [tag for tag, _ in Counter(all_tags).most_common(6)]

    # Split 3/3 for left/right sidebar
    left_tags = top_six[:3]
    right_tags = top_six[3:]

    return dict(left_tags=left_tags, right_tags=right_tags)