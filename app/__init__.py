from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from flask import g
from flask_login import current_user



db = SQLAlchemy()

def create_app():
    app = Flask(
        __name__,
        static_folder='../static',  # make sure path points to your project static/
        template_folder='../templates'
    )
    app.config.from_object("config.Config")

    db.init_app(app)

    from app.routes.home import home_bp
    from app.routes.products import products_bp
    from app.routes.admin import admin_bp
    from app.routes.login import login_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(login_bp)

    @app.context_processor
    def inject_globals():
        return {
            "current_user": getattr(g, "current_user", None),  # or current_user if Flask-Login installed
            "cart_items": [],
            "admin": False,
            "left_tags": ["Chocolate", "Caramel", "Wafer", "Bounty", "Snickers", "Tunnock's"],
            "right_tags": ["KitKat", "Mars", "Twix", "Galaxy", "Cadbury", "Lindt"],
        }

    return app