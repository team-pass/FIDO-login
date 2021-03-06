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

    # Page interaction info
    sessions = db.relationship('Session', lazy=True, backref=db.backref('user', lazy=True))

    def __repr__(self):
        return f'<User {self.display_name} {self.username}>'

    def set_password(self, password):
        '''Generates a salted & hashed password field for the user given a plaintext password'''
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        '''Checks if the given plaintext password matches the salt and hash for the given user'''
        return check_password_hash(self.password_hash, password)


class Session(db.Model):
    '''
    Model associating users with persistent cookie tokens;
    'user' property is implicitly created by relationship in User class
    '''

    id = db.Column(db.Integer, primary_key=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    token = db.Column(db.String(32), unique=True, nullable=False)
    
    interactions = db.relationship('Interaction', lazy=True, backref=db.backref('session', lazy=True))

    def __repr__(self):
        return f'<User id {self.user_id} has session token {self.token}>'
    
    
class Interaction(db.Model):
    '''
    Model associating persistent cookie token with individual page interactions;
    'session' property is implicitly created by relationship in Session class
    '''

    id = db.Column(db.Integer, primary_key=True)
    
    session_token = db.Column(db.String(32), db.ForeignKey('session.token'))
    event = db.Column(db.Enum('focus', 'click', 'submit'), nullable=False, validate_strings=True)
    page = db.Column(db.Enum('register', 'login'), nullable=False, validate_strings=True)
    timestamp = db.Column(db.DateTime, unique=False, nullable=False)

    def __repr__(self):
        return f'<Session token {self.session_token} triggered event {self.event} at {self.timestamp}> on page {self.page}'
