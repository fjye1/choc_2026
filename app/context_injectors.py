from flask import g

def inject_globals():
    """
    Provides global context variables to all templates.
    """
    return {
        "current_user": getattr(g, "current_user", None),  # or current_user if using Flask-Login
        "cart_items": [],
        "admin": False,
        "left_tags": ["Chocolate", "Caramel", "Wafer"],
        "right_tags": ["KitKat", "Mars", "Twix"],
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