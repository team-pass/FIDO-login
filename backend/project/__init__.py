#### BACKEND PROJECT PACKAGE INITIALIZATION ####


from flask import Flask
from flask_bcrypt import Bcrypt
import mysql.connector as mariadb
import os


# Create instance of Flask application
app = Flask(__name__, template_folder=os.path.abspath('../frontend'))
# Apparently setting `SECRET_KEY` helps against XSS
app.config['SECRET_KEY'] = 'a5cd2a20083251fa893622027c734d43'

# Create usable instance of encryptor
bcrypt = Bcrypt(app)

# Establish database connection
dbconnection = mariadb.connect(user='prod', password='changeme', database='team_pass', host='98.218.4.51')
dbcursor = dbconnection.cursor()


from project import routes


#### DEBUGGING ####


import sys, time


# Print message with timestamp to file (stderr by default)
def log(msg, sep='#', file_out=sys.stderr):
    print('%s\n(%s) %s\n%s' % (sep * 64, time.ctime(), msg, sep * 64), file=file_out)
