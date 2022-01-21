''' BACKEND PROJECT PACKAGE INITIALIZATION '''

import uuid
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask.sessions import SecureCookieSessionInterface
from .config import Config

# Create instance of Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Create own implementation of SessionInterface and set for app
class SecureCookieSessionInterfaceWithToken(SecureCookieSessionInterface):
    def open_session(self, app, request):
        session = super().open_session(app, request)
        if 'token' not in session:
            self.reset_session_token(session)
        return session

    def save_session(self, app, session, response):
        super().save_session(app, session, response)

    def reset_session_token(self, session):
        '''Reset the session token (used if the user deletes their account)'''
        session['token'] = str(uuid.uuid4())

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

# import declared routes
from . import routes, webauthn_routes

