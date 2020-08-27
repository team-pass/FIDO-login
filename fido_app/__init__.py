''' BACKEND PROJECT PACKAGE INITIALIZATION '''

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import mysql.connector as mariadb
from .utils import ensure_environ_vars
from dotenv import load_dotenv
import sys, time
import os

# Set the local environment based on a `backend/.env` file
load_dotenv()

# Throw a descriptive error if the user's environment variables are missing
ensure_environ_vars(
    [
        'FLASK_SECRET_KEY',
        'DB_USER',
        'DB_PASSWORD',
        'DB_NAME',
        'DB_HOST',
        'RP_ID',
        'RP_NAME',
        'ORIGIN',
    ]
)

# Create instance of Flask application
app = Flask(__name__)

# Apparently setting `SECRET_KEY` helps against XSS
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')

# Create instance of and initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)

# Adding CSRFProtection
csrf = CSRFProtect(app)

# Create usable instance of encryptor
bcrypt = Bcrypt(app)

# Establish database connection
dbconnection = mariadb.connect(
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME'),
    host=os.getenv('DB_HOST'),
)
dbcursor = dbconnection.cursor()


# import declared routes
from . import routes, webauthn_routes

