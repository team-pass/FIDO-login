#### BACKEND PROJECT PACKAGE INITIALIZATION ####


from flask import Flask
from flask_bcrypt import Bcrypt
import mysql.connector as mariadb


# Create instance of Flask application
app = Flask(__name__)
# Apparently setting `SECRET_KEY` helps against XSS
app.config['SECRET_KEY'] = 'a5cd2a20083251fa893622027c734d43'

# Create usable instance of encryptor
bcrypt = Bcrypt(app)

# Establish database connection
dbconnection = mariadb.connect(user='', password='', database='') # To be filled out
dbcursor = dbconnection.cursor()


from backend import routes
