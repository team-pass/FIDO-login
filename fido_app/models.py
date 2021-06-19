''' Contains all database models for SQLAlchemy '''
from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model, UserMixin):
    '''User model containing either biometric or password credentials'''

    id = db.Column(db.Integer, primary_key=True)

    # User info
    email = db.Column(db.String(80), unique=True, nullable=False)
    display_name = db.Column(db.String(160), unique=False, nullable=False)
    icon_url = db.Column(db.String(2083))
    high_score = db.Column(db.Integer, default=0)

    # Password info
    password_hash = db.Column(db.String(128))

    # Webauthn info
    credential_id = db.Column(db.String(250), unique=True, nullable=True)
    ukey = db.Column(db.String(20), unique=True, nullable=True)
    public_key = db.Column(db.String(65), unique=True, nullable=True)
    sign_count = db.Column(db.Integer, default=0)
    rp_id = db.Column(db.String(253), nullable=True)

    def __repr__(self):
        return f'<User {self.display_name} {self.username}>'

    def set_password(self, password):
        '''Generates a salted & hashed password field for the user given a plaintext password'''
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        '''Checks if the given plaintext password matches the salt and hash for the given user'''
        return check_password_hash(self.password_hash, password)
