''' ROUTING IMPLEMENTATION BASED ON DUO LABS'S '''

import os, sys, webauthn, secrets
from flask import (
    request,
    session,
    render_template,
    url_for,
    redirect,
    jsonify,
    make_response,
    flash,
)
from .models import User
from flask_login import login_required, login_user
from . import app, login_manager, db
from .utils import validate_email, get_first_result, get_display_name


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

    display_name = get_display_name(email)

    # Ensure the user's email isn't already in use (TODO: refactor into a function for
    # both registration stages)
    if User.query.filter_by(email=email).first():
        flash('Email address is already in use', 'error')
        return make_response(jsonify({'redirect': url_for('register')}), 401)

    # We strip the saved challenge of padding, so that we can do a byte
    # comparison on the URL-safe-without-padding challenge we get back
    # from the browser.
    # We will still pass the padded version down to the browser so that the JS
    # can decode the challenge into binary without too much trouble.
    challenge = secrets.token_urlsafe(32)
    ukey = secrets.token_urlsafe(20)
    session['registration'] = {
        'email': email,
        'display_name': display_name,
        'challenge': challenge.rstrip('='),
        'ukey': ukey,
    }

    make_credential_options = webauthn.WebAuthnMakeCredentialOptions(
        challenge=challenge,
        rp_name=RP_NAME,
        rp_id=RP_ID,
        user_id=ukey,
        username=email,
        display_name=display_name,
        icon_url='https://example.com',
    )

    return jsonify(make_credential_options.registration_dict)


@app.route('/webauthn/registration/verify-credentials', methods=['POST'])
def verify_registration_credentials():
    '''Verify the credential attestation generated during the registration process'''
    register_info = session['registration']
    challenge = register_info['challenge']
    ukey = register_info['ukey']
    email = register_info['email']
    display_name = register_info['display_name']
    registration_response = request.form

    # Craft the response from the
    webauthn_registration_response = webauthn.WebAuthnRegistrationResponse(
        rp_id=RP_ID,
        origin=ORIGIN,
        registration_response=registration_response,
        challenge=challenge,
        trust_anchor_dir=TRUST_ANCHOR_DIR,
        trusted_attestation_cert_required=True,
        self_attestation_permitted=True,
        none_attestation_permitted=True,
        uv_required=False,  # User Verification
    )

    try:
        webauthn_credential = webauthn_registration_response.verify()
    except Exception as e:
        flash(f'Registration failed. Error: {e}', 'error')
        return make_response(jsonify({'redirect': url_for('register')}), 401)

    # Step 17.
    #
    # Check that the credentialId is not yet registered to any other user.
    # If registration is requested for a credential that is already registered
    # to a different user, the Relying Party SHOULD fail this registration
    # ceremony, or it MAY decide to accept the registration, e.g. while deleting
    # the older registration.
    credential_id_exists = User.query.filter_by(
        credential_id=webauthn_credential.credential_id
    ).first()

    if credential_id_exists:
        flash('Credential ID already exists.', 'error')
        return make_response(jsonify({'redirect': url_for('register')}), 401)

    # Ensure the user's email isn't already in use (TODO: refactor into a function for
    # both registration stages)
    if User.query.filter_by(email=email).first():
        flash('Email address is already in use', 'error')
        return make_response(jsonify({'redirect': url_for('register')}), 401)

    # Create a new user
    user = User(
        ukey=ukey,
        email=email,
        display_name=display_name,
        public_key=webauthn_credential.public_key,
        credential_id=str(webauthn_credential.credential_id, "utf-8"),
        sign_count=webauthn_credential.sign_count,
        rp_id=RP_ID,
        icon_url='https://example.com',
    )
    db.session.add(user)
    db.session.commit()

    # Clear registration session info
    session.pop('registration', None)

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

    # Clear login session info
    session.pop('login', None)

    login_user(user)
    return jsonify({'redirect': url_for('profile')})
