from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


db = SQLAlchemy()
login_manager = LoginManager()


def safe_commit():
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise