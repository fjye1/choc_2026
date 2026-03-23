from flask import Flask
from .extensions import db, login_manager
from .context_injectors import inject_globals, inject_dummy_products, inject_top_tags, inject_cart_items
from app.utils.gravatar import gravatar_url
from flask_wtf import CSRFProtect
from app.routes.checkout import stripe_webhook

csrf = CSRFProtect()  # just create it here

def create_app():
    app = Flask(
        __name__,
        static_folder='../static',  # make sure path points to your project static/
        template_folder='../templates'
    )
    app.config.from_object("config.Config")

    csrf.init_app(app)
    csrf.exempt(stripe_webhook)
    db.init_app(app)
    login_manager.init_app(app)  # <-- here
    app.jinja_env.filters['gravatar'] = gravatar_url

    login_manager.login_view = "auth.login"  # redirect if not logged in
    login_manager.login_message_category = "info"

    from app.routes.home import home_bp
    from app.routes.products import product_bp
    from app.routes.admin import admin_bp
    from app.routes.auth import auth_bp
    from app.routes.profile import profile_bp
    from app.routes.orders import order_bp
    from app.routes.cart import cart_bp
    from app.routes.checkout import checkout_bp


    app.register_blueprint(home_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(checkout_bp)




    app.context_processor(inject_top_tags)
    app.context_processor(inject_cart_items) # so the cart icon changes if items in it


    return app

