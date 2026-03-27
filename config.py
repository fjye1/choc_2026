import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))  # loads .env into os.environ


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_INDIA")
    SECRET_KEY = os.environ.get("SECRET_KEY") # or "dev-secret-key"   fallback for dev
    CSFR_KEY = os.environ.get("CSFR")

    # Stripe keys
    STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")  # your secret key
    ENDPOINT_SECRET = os.environ.get("ENDPOINT_SECRET")
    DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")


    SQLALCHEMY_TRACK_MODIFICATIONS = False

