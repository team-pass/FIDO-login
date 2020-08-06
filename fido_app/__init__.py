''' BACKEND PROJECT PACKAGE INITIALIZATION '''

from flask import Flask
from flask_bcrypt import Bcrypt
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
    ['FLASK_SECRET_KEY', 'DB_USER', 'DB_PASSWORD', 'DB_NAME', 'DB_HOST',]
)

# Create instance of Flask application
app = Flask(__name__)

# Adding csrf protection
csrf = CSRFProtect(app)

# Apparently setting `SECRET_KEY` helps against XSS
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')

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
from . import routes

#### DEBUGGING ####

# Print message with timestamp to file (stderr by default)
def log(msg, sep='#', file_out=sys.stderr):
    print('%s\n(%s) %s\n%s' % (sep * 64, time.ctime(), msg, sep * 64), file=file_out)
