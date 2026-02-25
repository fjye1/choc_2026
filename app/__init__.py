from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, template_folder="../templates")
    app.config.from_object("config.Config")

    db.init_app(app)

    from app.routes.home import home_bp
    from app.routes.products import products_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(admin_bp)

    return app