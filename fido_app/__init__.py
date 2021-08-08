''' BACKEND PROJECT PACKAGE INITIALIZATION '''

from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from .config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_session import Session

# Create instance of Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Setup the database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Setup Flask-Sessions
Session(app)
app.config["SESSION_SQLALCHEMY"] = db

print(app.config)

# Create instance of and initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "error"

# Adding CSRFProtection
csrf = CSRFProtect(app)

# import declared routes
from . import routes, webauthn_routes

