''' BACKEND PROJECT PACKAGE INITIALIZATION '''

import uuid
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask.sessions import SecureCookieSessionInterface
from .config import Config
from .utils import get_credit

# Create instance of Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Create own implementation of SessionInterface and set for app
class SecureCookieSessionInterfaceWithToken(SecureCookieSessionInterface):
    def open_session(self, app, request):
        session = super().open_session(app, request)
        if 'token' not in session:
            session['token'] = str(uuid.uuid4())
        return session

    def save_session(self, app, session, response):
        super().save_session(app, session, response)

app.session_interface = SecureCookieSessionInterfaceWithToken()

# Setup the database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Create instance of and initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "error"

# Adding CSRFProtection
csrf = CSRFProtect(app)

# Expose some utility functions to templates for front-end convenience
app.jinja_env.globals.update(get_credit=get_credit)

# import declared routes
from . import routes, webauthn_routes

