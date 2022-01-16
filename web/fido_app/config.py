'''Flask app configuration'''
import os
from dotenv import load_dotenv
from .utils import get_database_uri_from

load_dotenv()

class Config(object):
    # Secret Key (for CSRF and session cookie stuff)
    SECRET_KEY = os.environ['FLASK_SECRET_KEY']

    # Database setup
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = get_database_uri_from(os.environ)

    # Webauthn setup
    RP_ID = os.environ['RP_ID']
    RP_NAME = os.environ['RP_NAME']
    ORIGIN = os.environ['ORIGIN']

