''' ROUTING IMPLEMENTATION BASED ON DUO LABS'S '''

import os, secrets
from datetime import date
from webauthn import (
    generate_registration_options, 
    verify_registration_response,
    generate_authentication_options, 
    verify_authentication_response,)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url, options_to_json
from webauthn.helpers.structs import AuthenticationCredential, PublicKeyCredentialDescriptor, RegistrationCredential
from webauthn.helpers.exceptions import InvalidAuthenticationResponse, InvalidRegistrationResponse
from flask import (
    request,
    session,
    url_for,
    redirect,
    jsonify,
    make_response,
    flash,
)
from .models import User, LoginAttempts
from flask_login import current_user, login_user
from . import app, db
from .utils import get_display_name, validate_email, get_elapsed_days, append_to_login_bitfield


RP_ID = os.getenv('RP_ID')
RP_NAME = os.getenv('RP_NAME')
ORIGIN = os.getenv('ORIGIN')

@app.route('/webauthn/registration/start', methods=['POST'])
def webauthn_registration_start():
    """Starts the webauthn registration process by sending the user a random challenge"""

    # Behavior depends on whether the user is logged in and trying to add a new biometric or not
    # Retrieve email from current_user if logged in, or from registration form if a first-time user
    if current_user.is_authenticated:
        email = current_user.email
    else:
        # MakeCredentialOptions
        email = request.form['email']

        # Verify that email and display name are acceptable
        # TODO: improve error screen (likely using flashing)
        if not validate_email(email):
            flash('Invalid email', 'error')
            return make_response(jsonify({'redirect': url_for('register')}), 401)

        # Ensure the user's email isn't already in use (TODO: refactor into a function for
        # both registration stages)
        if User.query.filter_by(email=email).first():
            flash('Email address is already in use', 'error')
            return make_response(jsonify({'redirect': url_for('register')}), 401)

    ukey = secrets.token_urlsafe(20)
    display_name = get_display_name(email)
    
    registration_options = generate_registration_options(
        rp_name=RP_NAME,
        rp_id=RP_ID,
        user_id=ukey,
        user_name=email,
        user_display_name=display_name
    )

    session['registration'] = {
        'email': email,
        'challenge': bytes_to_base64url(registration_options.challenge),
        'ukey': ukey,
        'display_name': display_name,
    }

    return options_to_json(registration_options)


@app.route('/webauthn/registration/verify-credentials', methods=['POST'])
def verify_registration_credentials():
    '''Verify the credential attestation generated during the registration process'''
    register_info = session['registration']
    challenge = register_info['challenge']
    ukey = register_info['ukey']
    email = register_info['email']
    display_name = register_info['display_name']

    # The form data is sent back as JSON-encoded text with a MIME type of 'text/plain' (stored
    # in `request.data`). Even though `application/json` would be a more accurate MIME type,
    # using `text-plain` allows us to call the built-in `RegistrationCredential.parse_raw` method.
    credential = RegistrationCredential.parse_raw(request.data)

    # Clear registration session info before doing anything (prevents replays)
    session.pop('registration', None)

    try:
       verified_registration = verify_registration_response(
            credential=credential,
            expected_challenge=base64url_to_bytes(challenge),
            expected_rp_id=RP_ID,
            expected_origin=ORIGIN,
            require_user_verification=True
        )
    except InvalidRegistrationResponse as e:
        flash(f'Registration failed. Error: {e}', 'error')
        return make_response(jsonify({'redirect': url_for('register')}), 401)

    # Step 17.
    #
    # Check that the credentialId is not yet registered to any other user.
    # If registration is requested for a credential that is already registered
    # to a different user, the Relying Party SHOULD fail this registration
    # ceremony, or it MAY decide to accept the registration, e.g. while deleting
    # the older registration.
    credential_id = bytes_to_base64url(verified_registration.credential_id)
    if User.query.filter_by(credential_id=credential_id).first():
        flash('Credential ID already exists.', 'error')
        return make_response(jsonify({'redirect': url_for('register')}), 401)

    # If this is an existing user, update the db entry for that user
    if current_user.is_authenticated:
        current_user.ukey = ukey
        current_user.public_key = bytes_to_base64url(verified_registration.credential_public_key)
        current_user.credential_id = credential_id
        current_user.sign_count = verified_registration.sign_count
        current_user.authenticator_id = verified_registration.aaguid
        current_user.attestation_format = verified_registration.fmt
        current_user.user_verified = verified_registration.user_verified

        db.session.commit()

    # Create a new User entry in db if this is a first-time user
    else:
        # Ensure the user's email isn't already in use
        # (TODO: refactor into a function for both registration stages)
        if User.query.filter_by(email=email).first():
            flash('Email address is already in use', 'error')
            return make_response(jsonify({'redirect': url_for('register')}), 401)

        # Create a new user
        user = User(
            email=email,
            ukey=ukey,
            display_name=display_name,
            last_complete_login=date.today(),
            login_bitfield=0,
            public_key=bytes_to_base64url(verified_registration.credential_public_key),
            credential_id=credential_id,
            sign_count=verified_registration.sign_count,
            authenticator_id=verified_registration.aaguid,
            attestation_format=verified_registration.fmt,
            user_verified=verified_registration.user_verified
        )
        db.session.add(user)
        db.session.commit()

        # TODO: look into a single commit (not sure if possible)
        user.add_session(session, commit=True)

    if current_user.is_authenticated:
        flash(f'Successfully registered biometric')
    else:
        flash(f'Successfully registered with email {email}')
        login_user(user, remember=False)

    return jsonify({'redirect': url_for('profile')})


@app.route('/webauthn/login/start', methods=['POST'])
def webauthn_login_start():
    '''Start the biometric login process by generating a random challenge for the user'''
    email = request.form['email']

    if not validate_email(email):
        flash('Please enter a valid email', 'error')
        return make_response(jsonify({'redirect': url_for('login')}), 401)

    # Attempt to find user in database
    user = User.query.filter_by(email=email).first()
    if user and user.credential_id:
        credential_id_bytes = base64url_to_bytes(user.credential_id)
        authentication_options = generate_authentication_options(
            rp_id=RP_ID,
            allow_credentials=[PublicKeyCredentialDescriptor(id=credential_id_bytes)],
        )
    else:
        # Prepare nonsense options so we can still proceed to verification step
        # This helps hide the true point of failure during WebAuthn authentication
        authentication_options = generate_authentication_options(
            rp_id=RP_ID,
            allow_credentials=[PublicKeyCredentialDescriptor(id=bytes(1))],
        )

    session['login'] = {
        'challenge': bytes_to_base64url(authentication_options.challenge),
        'email': email
    }

    return options_to_json(authentication_options)


@app.route('/webauthn/login/verify-assertion', methods=['POST'])
def webauthn_verify_login():
    '''Verify the user's credential attesttion during the login process'''
    challenge = session['login']['challenge']
    email = session['login']['email']

    # The form data is sent back as JSON-encoded text with a MIME type of 'text/plain' (stored
    # in `request.data`). Even though `application/json` would be a more accurate MIME type,
    # using `text-plain` allows us to call the built-in `RegistrationCredential.parse_raw` method.
    credential = AuthenticationCredential.parse_raw(request.data)

    # Attempt to find a matching user and obtain fields necessary for authentication
    user = User.query.filter_by(credential_id=credential.id).first()
    if user:
        pub_key = user.public_key
        sign_count = user.sign_count
    else:
        # Prepare invalid values for authentication to obfuscate point of failure
        pub_key = ''
        sign_count = 0

    # Get existing login attempt db entry or create new one
    attempts = LoginAttempts.query.filter_by(email=email, date=date.today()).first()
    if not attempts:
        attempts = LoginAttempts(
            email=email,
            date=date.today(),
            password_successes=0,
            password_failures=0,
            fido_successes=0,
            fido_failures=0
        )

    try:
        authenitication_verification = verify_authentication_response(
            credential=credential,
            expected_challenge=base64url_to_bytes(challenge),
            expected_rp_id=RP_ID,
            expected_origin=ORIGIN,
            credential_public_key=base64url_to_bytes(pub_key),
            credential_current_sign_count=sign_count,
            require_user_verification=True
        )
    except InvalidAuthenticationResponse as e:
        # Update failed login count
        attempts.fido_failures += 1
        db.session.add(attempts)
        db.session.commit()
        
        flash(f'Authentication failed. Error: {e}', 'error')
        return make_response(jsonify({'redirect': url_for('login')}), 401)

    if user:
        # Update counter.
        user.sign_count = authenitication_verification.new_sign_count
    
        # Update login trackers
        if user.last_complete_login != date.today():
            if 'logged_in_today' in session and session['logged_in_today'] == 'password':
                del session['logged_in_today']
                user.login_bitfield = append_to_login_bitfield(
                    user.login_bitfield,
                    get_elapsed_days(user.last_complete_login)
                )
                user.last_complete_login = date.today()
            else:
                session['logged_in_today'] = 'fido2'
    
        db.session.add(user)
        db.session.commit()
        user.add_session(session, commit=True)

        # Update successful login count
        attempts.fido_successes += 1
        db.session.add(attempts)
        db.session.commit()

        # Clear login session info
        session.pop('login', None)

        login_user(user)
        return jsonify({'redirect': url_for('profile')})

    flash(f'Authentication failed.', 'error')
    return make_response(jsonify({'redirect': url_for('login')}), 401)
