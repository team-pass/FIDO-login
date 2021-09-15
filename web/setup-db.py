"""Using the info from the migrations directory, 
create a database with all of the correct tables"""
from fido_app import app
from flask_migrate import upgrade

with app.app_context():
    upgrade()