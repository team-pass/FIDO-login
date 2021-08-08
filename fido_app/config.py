'''Flask app configuration'''
import os
from .utils import ensure_environ_vars
from dotenv import load_dotenv

# Throw a descriptive error if the user's environment variables are missing
load_dotenv()
ensure_environ_vars(
    [
        'FLASK_SECRET_KEY',
        'DATABASE_URL',
        'RP_ID',
        'RP_NAME',
        'ORIGIN',
        'TRUST_ANCHOR_DIR',
    ]
)


class Config(object):
    # Secret Key (for CSRF and session cookie stuff)
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY')

    # Database setup
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Webauthn setup
    RP_ID = os.getenv('RP_ID')
    RP_NAME = os.getenv('RP_NAME')
    ORIGIN = os.getenv('ORIGIN')
    TRUST_ANCHOR_DIR = os.getenv('TRUST_ANCHOR_DIR')

    # Flask Sessions
    SESSION_TYPE = 'sqlalchemy'
    SESSION_COOKIE_SECURE = True
    SESSION_USE_SIGNER = True
    SESSION_SQLALCHEMY_TABLE = 'sessions'

