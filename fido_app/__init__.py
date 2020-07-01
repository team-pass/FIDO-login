''' BACKEND PROJECT PACKAGE INITIALIZATION '''

from flask import Flask
from flask_bcrypt import Bcrypt
import mysql.connector as mariadb
from dotenv import load_dotenv
import sys, time
import os

# Set the local environment based on a `backend/.env` file
load_dotenv()

# Create instance of Flask application
app = Flask(__name__)
# Apparently setting `SECRET_KEY` helps against XSS
app.config['SECRET_KEY'] = os.getenv('Flask_SECRET_KEY')

# Create usable instance of encryptor
bcrypt = Bcrypt(app)

# Establish database connection
dbconnection = mariadb.connect(
    user=os.getenv('db_user'),
    password=os.getenv('db_pass'),
    database='team_pass',
    host='98.218.4.51',
)
dbcursor = dbconnection.cursor()

# import declared routes
from . import routes

#### DEBUGGING ####

# Print message with timestamp to file (stderr by default)
def log(msg, sep='#', file_out=sys.stderr):
    print('%s\n(%s) %s\n%s' % (sep * 64, time.ctime(), msg, sep * 64), file=file_out)
