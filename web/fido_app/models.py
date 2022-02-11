''' Contains all database models for SQLAlchemy '''
from . import db
import logging
from flask_login import UserMixin
from webauthn.helpers.structs import AttestationFormat
from werkzeug.security import generate_password_hash, check_password_hash

logger = logging.getLogger(__name__)
class Session(db.Model):
    '''
    Model associating users with persistent cookie tokens;
    'user' property is implicitly created by relationship in User class
    '''

    token = db.Column(db.String(40), primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='sessions')

    interactions = db.relationship('Interaction')

    def __repr__(self):
        return f'<User id {self.user_id} has session token {self.token}>'

class User(db.Model, UserMixin):
    '''User model containing either biometric or password credentials'''
    id = db.Column(db.Integer, primary_key=True)

    # User info
    email = db.Column(db.String(80), unique=True)
    display_name = db.Column(db.String(80))
    high_score = db.Column(db.Integer, default=0)

    # Password info
    password_hash = db.Column(db.String(128))

    # Webauthn info
    # TODO: move into separate table
    credential_id = db.Column(db.String(400), unique=True)
    ukey = db.Column(db.String(32), unique=True)
    public_key = db.Column(db.String(65), unique=True)
    sign_count = db.Column(db.Integer, default=0)
    authenticator_id = db.Column(db.String(40))
    user_verified = db.Column(db.Boolean(), default=False)

    # Values_callable is needed to allow alembic to generate a correct
    # migration script
    attestation_format = db.Column(db.Enum(AttestationFormat, validate_strings=True, values_callable=lambda x: [e.value for e in x]))

    # Page interaction info
    sessions = db.relationship('Session', back_populates='user')

    def __repr__(self):
        return f'<User {self.email}>'

    def set_password(self, password):
        '''Generates a salted & hashed password field for the user given a plaintext password'''
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        '''Checks if the given plaintext password matches the salt and hash for the given user'''
        return check_password_hash(self.password_hash, password)

    def has_password(self):
        return self.password_hash is not None

    def add_session(self, session: Session, commit=False):
        '''Associates the session with the given id to this particular user'''

        # Don't add a session token that already exists
        if Session.query.filter_by(token=session["token"]).first():
            logger.info(f"Session already being tracked, not adding to {self}")
            return

        new_session = Session(
            token=session["token"],
            user_id=self.id,
        )

        db.session.add(new_session)

        if commit:
            db.session.commit()

    def delete_identifiable_info(self):
        '''
        Removes any identifiable information from the user profile, preserving the user's ID. The 
        benefit of this is to keep track of their old interactions while deleting their account info.
        It also allows us to save any anonymized user data associated with the interactions.
        '''
        # User info
        self.email = None
        self.display_name = None
        self.high_score = None

        # Password info
        self.password_hash = None

        # Webauthn info
        self.credential_id = None
        self.ukey = None
        self.public_key = None
        self.sign_count = 0
        self.authenticator_id = None
        self.user_verified = False
        self.attestation_format = None
    
class Interaction(db.Model):
    '''
    Model associating persistent cookie token with individual page interactions;
    'session' property is implicitly created by relationship in Session class
    '''

    id = db.Column(db.Integer, primary_key=True)
    
    session_token = db.Column(db.String(40), db.ForeignKey('session.token'))
    element = db.Column(db.String(32), nullable=False)
    event = db.Column(db.Enum('focus', 'click', 'submit', validate_strings=True), nullable=False)
    page = db.Column(db.Enum('/register', '/login', validate_strings=True), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    group_id = db.Column(db.String(40), nullable=False)

    def __repr__(self):
        return f'<Session token {self.session_token} triggered event {self.event} at {self.timestamp}> on page {self.page}'
