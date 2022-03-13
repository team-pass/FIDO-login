''' Contains all database models for SQLAlchemy '''
from .utils import get_random_session_token
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

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
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

    # Saves the last date the user logged in with both a password and FIDO2
    last_complete_login = db.Column(db.Date)
    # Each bit, starting with the least significant bit,
    # represents a new day since account registration.
    # A 1 represents a day in which the user logged in;
    # a 0 represents a skipped day.
    # E.g., if a user registers on Mar. 1st and then
    # logs in on the 3rd, 4th, and 6th, `login_bitfield`
    # should store 22 (10110 in binary).
    # Overflow occurs after 32 days. Change to db.BigInteger if necessary.
    login_bitfield = db.Column(db.Integer, default=0)

    # Password info
    password_hash = db.Column(db.String(128))

    # Webauthn info
    # TODO: move into separate table
    credential_id = db.Column(db.String(400), unique=True)
    ukey = db.Column(db.String(32), unique=True)
    public_key = db.Column(db.String(400), unique=True)
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

    def add_session(self, flask_session, commit=False):
        '''Associates the session with the given id to this particular user'''
        session = Session.query.filter_by(token=flask_session["token"]).first()

        if session and session.user_id == self.id:
            logger.info(f"Session already being tracked for {session.user}.")
            return

        if session and session.user_id != self.id:
            logger.warn(f"This session token is attached to {session.user}, but is also being used by {self}!"
                + "Creating a fresh session token for {self}.")
            
            # Create a fresh session token for the current user (that isn't stored in the DB currently)
            # TODO: figure out how to prevent the most recent batch of interactions from being 
            # misattributed to the old user that this session token was attached to.
            # Alternatively, we could just make the session tokens less persistent
            flask_session["token"] = get_random_session_token()
            session = None

        if session:
            logger.info(f"Attaching existing session to {self}")
            session.user_id = self.id
        else:
            logger.info(f"Attaching new session to {self}")
            session = Session(
                token=flask_session["token"],
                user_id=self.id,
            )

        db.session.add(session)

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

        # Compensation info
        self.last_complete_login = None
        self.login_bitfield = 0

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
    event = db.Column(db.Enum('focus', 'click', 'submit', 'load', validate_strings=True), nullable=False)
    login_method = db.Column(db.Enum('did not attempt', 'fido', 'password', validate_strings=True), nullable=False)
    page = db.Column(db.Enum('/register', '/login', '/add-password', validate_strings=True), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    group_id = db.Column(db.String(40), nullable=False)

    def __repr__(self):
        return f'<Session token {self.session_token} triggered event {self.event} at {self.timestamp}> on page {self.page}'

class LoginAttempts(db.Model):
    '''
    Model associating email and date with login attempt counts,
    both successful and not.
    '''

    id = db.Column(db.Integer, primary_key=True)

    # Identifiers
    email = db.Column(db.String(80), nullable=False)
    date = db.Column(db.Date, nullable=False)

    # Counters
    password_successes = db.Column(db.Integer, default=0)
    password_failures = db.Column(db.Integer, default=0)
    fido_successes = db.Column(db.Integer, default=0)
    fido_failures = db.Column(db.Integer, default=0)
