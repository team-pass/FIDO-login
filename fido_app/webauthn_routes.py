''' ROUTING IMPLEMENTATION BASED ON DUO LABS'S '''

import os, sys, webauthn, secrets, json
from webauthn import (
    generate_registration_options, 
    verify_registration_response,
    generate_authentication_options, 
    verify_authentication_response,)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url, options_to_json
from webauthn.helpers.structs import RegistrationCredential
from webauthn.helpers.exceptions import InvalidRegistrationResponse
from flask import (
    request,
    session,
    url_for,
    redirect,
    jsonify,
    make_response,
    flash,
)
from .models import User
from flask_login import login_user
from . import app, db
from .utils import get_display_name, validate_email


RP_ID = os.getenv('RP_ID')
RP_NAME = os.getenv('RP_NAME')
ORIGIN = os.getenv('ORIGIN')

# Trust anchors (trusted attestation roots) should be
# placed in TRUST_ANCHOR_DIR.
TRUST_ANCHOR_DIR = os.getenv('TRUST_ANCHOR_DIR')


@app.route('/webauthn/registration/start', methods=['POST'])
def webauthn_registration_start():
    """Starts the webauthn registration process by sending the user a random challenge"""

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
        'display_name': display_name
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
    data = request.data
    print(data)
    credential = RegistrationCredential.parse_raw(data)

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

    # Ensure the user's email isn't already in use (TODO: refactor into a function for
    # both registration stages)
    if User.query.filter_by(email=email).first():
        flash('Email address is already in use', 'error')
        return make_response(jsonify({'redirect': url_for('register')}), 401)

    # Create a new user
    user = User(
        email=email,
        ukey=ukey,
        display_name=display_name,
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

    flash(f'Successfully registered with email {email}')
    return jsonify({'redirect': url_for('login')})


@app.route('/webauthn/login/start', methods=['POST'])
def webauthn_login_start():
    '''Start the biometric login process by generating a random challenge for the user'''
    email = request.form['email']

    if not validate_email(email):
        flash('Please enter a valid email', 'error')
        return make_response(jsonify({'redirect': url_for('login')}), 401)

    # Attempt to find user in database
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User does not exist', 'error')
        return make_response(jsonify({'redirect': url_for('login')}), 401)
    if not user.credential_id:
        flash('User does not have biometric to sign in with', 'error')
        return make_response(jsonify({'redirect': url_for('login')}), 401)

    # We strip the padding from the challenge stored in the session
    # for the reasons outlined in the comment in webauthn_begin_activate.
    challenge = secrets.token_urlsafe(32)
    session['login'] = {'challenge': challenge.rstrip('=')}

    webauthn_user = webauthn.WebAuthnUser(
        user_id=user.ukey,
        username=user.email,
        display_name=user.display_name,
        icon_url=user.icon_url,
        credential_id=user.credential_id,
        public_key=user.public_key,
        sign_count=user.sign_count,
        rp_id=user.rp_id,
    )

    webauthn_assertion_options = webauthn.WebAuthnAssertionOptions(
        webauthn_user, challenge
    )

    return jsonify(webauthn_assertion_options.assertion_dict)


@app.route('/webauthn/login/verify-assertion', methods=['POST'])
def webauthn_verify_login():
    '''Verify the user's credential attesttion during the login process'''
    challenge = session['login']['challenge']
    assertion_response = request.form
    credential_id = assertion_response.get('id')

    # Ensure a matching user exists
    user = User.query.filter_by(credential_id=credential_id).first()
    if not user:
        flash('User does not exist')
        return make_response(jsonify({'redirect': url_for('login')}), 401)

    # TODO: determine if this info should be stored at the session level
    webauthn_user = webauthn.WebAuthnUser(
        user_id=user.ukey,
        username=user.email,
        display_name=user.display_name,
        icon_url=user.icon_url,
        credential_id=user.credential_id,
        public_key=user.public_key,
        sign_count=user.sign_count,
        rp_id=user.rp_id,
    )

    webauthn_assertion_response = webauthn.WebAuthnAssertionResponse(
        webauthn_user=webauthn_user,
        assertion_response=assertion_response,
        challenge=challenge,
        origin=ORIGIN,
        uv_required=False,
    )  # User Verification

    try:
        sign_count = webauthn_assertion_response.verify()
    except Exception as e:
        flash(f'Assertion failed. Error: {e}')
        return make_response(jsonify({'redirect': url_for('login')}), 401)

    # Update counter.
    user.sign_count = sign_count
    db.session.add(user)
    db.session.commit()
    user.add_session(session, commit=True)

    # Clear login session info
    session.pop('login', None)

    login_user(user)
    return jsonify({'redirect': url_for('profile')})
