""" BACKEND PROJECT PACKAGE INITIALIZATION """

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import mysql.connector as mariadb
from dotenv import load_dotenv
import os

# Set the local environment based on a `backend/.env` file
load_dotenv()

# Create instance of Flask application
app = Flask(__name__, template_folder=os.path.abspath('../frontend'))
# Apparently setting `SECRET_KEY` helps against XSS
app.config['SECRET_KEY'] = os.getenv('Flask_SECRET_KEY')

# Create instance of and initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)

# Create usable instance of encryptor
bcrypt = Bcrypt(app)

# Establish database connection
dbconnection = mariadb.connect(user=os.getenv('db_user'), password=os.getenv('db_pass'), database='team_pass', host='98.218.4.51')
dbcursor = dbconnection.cursor()


#from project import routes


''' USER CLASS (for use with Flask-Login) '''


from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, email, display_name, ukey, icon_url, credential_id, pub_key, sign_count, rp_id):
        self.email = email                  # str
        self.display_name = display_name    # str
        self.ukey = ukey                    # str
        self.icon_url = icon_url            # str
        self.credential_id = credential_id  # str
        self.pub_key = pub_key              # str
        self.sign_count = sign_count        # int
        self.rp_id = rp_id                  # str

    def __repr__(self):
        return 'User %s (Email: %s)' % (self.display_name, self.email)


''' UTILITY  '''


import re


def validate_email(email):
    return isinstance(email, str) and re.search('^([a-z0-9]+[\._]?)*[a-z0-9]+@\w+\.\w+$', email) is not None


def validate_display_name(name):
    return isinstance(name, str) and re.search('\w') is not None


''' DEBUGGING '''


import sys, time


# Print message with timestamp to file (stderr by default)
def log(msg, sep='#', file_out=sys.stderr):
    print('%s\n(%s) %s\n%s' % (sep * 64, time.ctime(), msg, sep * 64), file=file_out)
