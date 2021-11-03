''' ROUTING IMPLEMENTATION BASED ON DUO LABS'S '''

import os, sys, secrets
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
from .utils import validate_email, get_display_name, recursively_b64_encode
from base64 import b64encode

from fido2.webauthn import PublicKeyCredentialRpEntity
from fido2.client import ClientData
from fido2.server import Fido2Server
from fido2.ctap2 import AttestationObject, AuthenticatorData
from fido2 import cbor
from flask import Flask, session, request, redirect, abort

RP_ID = os.getenv('RP_ID')
RP_NAME = os.getenv('RP_NAME')
ORIGIN = os.getenv('ORIGIN')

# Trust anchors (trusted attestation roots) should be
# placed in TRUST_ANCHOR_DIR.
TRUST_ANCHOR_DIR = os.getenv('TRUST_ANCHOR_DIR')

rp = PublicKeyCredentialRpEntity(RP_ID, RP_NAME)
server = Fido2Server(rp)
credentials = []

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
    # challenge = secrets.token_urlsafe(32)
    ukey = secrets.token_urlsafe(20)

    """
    registration_data format:
    {
        'publicKey': PublicKeyCredentialCreationOptions({
            'rp': PublicKeyCredentialRpEntity({
                'id': 'localhost',
                'name': 'team-pass/fido-login'
            }),
            'user': PublicKeyCredentialUserEntity({
                'id': ukey<str>,
                'name': email<str>,
                'icon': 'https://example.com/image.png',
                'displayName': display_name<str>
            }),
            'challenge': <bytes>,
            'pubKeyCredParams': [
                PublicKeyCredentialParameters({
                    'type': <PublicKeyCredentialType.PUBLIC_KEY: 'public-key'>,
                    'alg': -7
                }),
                PublicKeyCredentialParameters({
                    'type': <PublicKeyCredentialType.PUBLIC_KEY: 'public-key'>,
                    'alg': -8
                }),
                PublicKeyCredentialParameters({
                    'type': <PublicKeyCredentialType.PUBLIC_KEY: 'public-key'>,
                    'alg': -37
                }),
                PublicKeyCredentialParameters({
                    'type': <PublicKeyCredentialType.PUBLIC_KEY: 'public-key'>,
                    'alg': -257
                })
            ],
            'excludeCredentials': [
            ],
            authenticatorSelection': AuthenticatorSelectionCriteria({
                'authenticatorAttachment': <AuthenticatorAttachment.CROSS_PLATFORM: 'cross-platform'>,
                'userVerification': <UserVerificationRequirement.DISCOURAGED: 'discouraged'>
            })
        })
    }
    state format:
    {
        'challenge': <str>,
        'user_verification': 'discouraged'
    }
    """
    #print(f'\ncredentials = {credentials}\n', file=sys.stderr)
    registration_data, state = server.register_begin(
        {
            "id": ukey,
            "name": email,
            "displayName": display_name,
            "icon": "https://example.com/image.png",
        },
        credentials=credentials,
        user_verification="discouraged",
        authenticator_attachment="cross-platform",
        # challenge=challenge,
    )
    # credentials list is not updated by register_begin()

    registration_data = recursively_b64_encode(registration_data)
    challenge = registration_data['publicKey']['challenge']
    
    print(f"\nregistration_data = {registration_data}\n", file=sys.stderr)
    print(f"\nstate = {session['state']}\n", file=sys.stderr)
    print(f'\ncredentials = {credentials}\n', file=sys.stderr)

    session["state"] = state
    session['registration'] = {
        'email': email,
        'display_name': display_name,
        'challenge': challenge,
        'ukey': ukey,
    }
    
    return jsonify(registration_data)


@app.route('/webauthn/registration/verify-credentials', methods=['POST'])
def verify_registration_credentials():
    """Verify the credential attestation generated during the registration process"""

    register_info = session['registration']
    ukey = register_info['ukey']
    email = register_info['email']
    display_name = register_info['display_name']
    challenge = register_info['challenge']
    #registration_response = request.form

    data = cbor.decode(request.get_data())
    client_data = ClientData(data["clientDataJSON"])
    att_obj = AttestationObject(data["attestationObject"])

    credential_id_exists = User.query.filter_by(
        credential_id=webauthn_credential.credential_id
    ).first()

    if credential_id_exists:
        flash('Credential ID already exists.', 'error')
        return make_response(jsonify({'redirect': url_for('register')}), 401)

    auth_data = server.register_complete(session["state"], client_data, att_obj)

    # Add credentials to database
    credentials.append(auth_data.credential_data)

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
        public_key='',  # not needed anymore?
        credential_id='',  # also not needed?
        sign_count=webauthn_credential.sign_count,  # how to obtain?
        rp_id=RP_ID,
        icon_url='https://example.com',
    )
    db.session.add(user)
    db.session.commit()

    # Clear registration session info
    session.pop('registration', None)

    flash(f'Successfully registered with email {email}')

    return cbor.encode({'status': 'OK'})


@app.route('/webauthn/login/start', methods=['POST'])
def webauthn_login_start():
    """Start the biometric login process by generating a random challenge for the user"""
    
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

    """
    auth_data format:
    {
        'publicKey': PublicKeyCredentialRequestOptions({
            'challenge': <bytes>,
            'rpId': 'localhost',
            'allowCredentials': [
            ]
        })
    }
    state format:
    {
        'challenge': <str>,
        'user_verification': None
    }
    """
    auth_data, state = server.authenticate_begin(credentials)
    # credentials list is not updated by authenticate_begin()
    
    session['state'] = state

    return cbor.encode(auth_data)


@app.route('/webauthn/login/verify-assertion', methods=['POST'])
def webauthn_verify_login():
    """Verify the user's credential attesttion during the login process"""
    
    challenge = session['login']['challenge']
    assertion_response = request.form
    credential_id = assertion_response.get('id')

    # Ensure a matching user exists
    user = User.query.filter_by(credential_id=credential_id).first()
    if not user:
        flash('User does not exist')
        return make_response(jsonify({'redirect': url_for('login')}), 401)

    data = cbor.decode(request.get_data())
    credential_id = data['credentialId']
    client_data = ClientData(data['clientDataJSON'])
    auth_data = AuthenticatorData(data['authenticatorData'])
    signature = data['signature']

    server.authenticate_complete(
        session.pop('state'),
        credentials,
        credential_id,
        client_data,
        auth_data,
        signature,
    )

    try:
        sign_count = webauthn_assertion_response.verify()
    except Exception as e:
        flash(f'Assertion failed. Error: {e}')
        return make_response(jsonify({'redirect': url_for('login')}), 401)

    # Update counter
    user.sign_count = sign_count
    db.session.add(user)
    db.session.commit()

    # Clear login session info
    session.pop('login', None)

    login_user(user)
    
    return cbor.encode({'status': 'OK'})
