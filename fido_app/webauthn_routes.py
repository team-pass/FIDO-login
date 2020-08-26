''' ROUTING IMPLEMENTATION BASED ON DUO LABS'S '''

import os, sys, webauthn, secrets
from flask import request, session, render_template, url_for, redirect, jsonify, make_response
from flask_login import login_required
from . import app, bcrypt, dbconnection, dbcursor, login_manager
from .utils import validate_email, validate_display_name, log


RP_ID = os.getenv('RP_ID')
RP_NAME = os.getenv('RP_NAME')
RP_ORIGIN = os.getenv('ORIGIN')


@login_manager.user_loader
def load_user(user_id):
    try:
        id = int(user_id)
    except ValueError:
        return None
    return User.query.get(id)


@app.route('/webauthn_begin_activate', methods=['POST'])
def webauthn_begin_activate():
    # MakeCredentialOptions
    email = request.form['register_email']
    display_name = request.form['register_display_name']

    # Verify that email and display name are acceptable
    if not validate_email(email):
        return make_response(jsonify({'fail': 'Invalid email.'}), 401)
    if not validate_display_name(display_name):
        return make_response(jsonify({'fail': 'Invalid display name.'}), 401)

    # Check if email is already taken
    #dbcursor.execute('SELECT email FROM test WHERE email = %s', (email,))
    #user = dbcursor.fetchone()
    #if user:
    dbcursor.callproc('user_select_users', args=(email,))
    if get_first_result(dbcursor):
        return make_response(jsonify({'fail': 'User already exists.'}), 401)

    # Clear session variables prior to starting a new registration
    if 'register_ukey' in session:
        session.pop('register_ukey', None)
    if 'register_email' in session:
        session.pop('register_email', None)
    if 'register_display_name' in session:
        session.pop('register_display_name', None)
    if 'challenge' in session:
        session.pop('challenge', None)

    session['register_email'] = email
    session['register_display_name'] = display_name

    challenge = secrets.token_urlsafe(32)
    ukey = secrets.token_urlsafe(20)

    # We strip the saved challenge of padding, so that we can do a byte
    # comparison on the URL-safe-without-padding challenge we get back
    # from the browser.
    # We will still pass the padded version down to the browser so that the JS
    # can decode the challenge into binary without too much trouble.
    session['challenge'] = challenge.rstrip('=')
    session['register_ukey'] = ukey

    make_credential_options = webauthn.WebAuthnMakeCredentialOptions(
        challenge, RP_NAME, RP_ID, ukey, email, display_name,
        'https://example.com')

    return jsonify(make_credential_options.registration_dict)


@app.route('/webauthn_begin_assertion', methods=['POST'])
def webauthn_begin_assertion():
    email = request.form['login_username']

    if not validate_email(email):
        return make_response(jsonify({'fail': 'Invalid email.'}), 401)

    # Attempt to find user in database (TODO: replace with future stored proc)
    dbcursor.execute('SELECT email, display_name, ukey, icon_url, credential_id, pub_key, sign_count, rp_id FROM test WHERE email = %s', (email,))
    user = dbcursor.fetchone()

    if not user:
        return make_response(jsonify({'fail': 'User does not exist.'}), 401)
    if not result[4]:
        return make_response(jsonify({'fail': 'Unknown credential ID.'}), 401)

    session.pop('challenge', None)

    challenge = secrets.token_urlsafe(32)

    # We strip the padding from the challenge stored in the session
    # for the reasons outlined in the comment in webauthn_begin_activate.
    session['challenge'] = challenge.rstrip('=')

    webauthn_user = webauthn.WebAuthnUser(
        user[2], # user.ukey
        user[0], # user.username (or email in our case)
        user[1], # user.display_name
        user[3], # user.icon_url
        user[4], # user.credential_id
        user[5], # user.pub_key
        user[6], # user.sign_count
        user[7]) # user.rp_id

    webauthn_assertion_options = webauthn.WebAuthnAssertionOptions(
        webauthn_user, challenge)

    return jsonify(webauthn_assertion_options.assertion_dict)


@app.route('/verify_credential_info', methods=['POST'])
def verify_credential_info():
    challenge = session['challenge']
    email = session['register_email']
    display_name = session['register_display_name']
    ukey = session['register_ukey']

    registration_response = request.form
    trust_anchor_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), TRUST_ANCHOR_DIR)
    trusted_attestation_cert_required = True
    self_attestation_permitted = True
    none_attestation_permitted = True

    webauthn_registration_response = webauthn.WebAuthnRegistrationResponse(
        RP_ID,
        ORIGIN,
        registration_response,
        challenge,
        trust_anchor_dir,
        trusted_attestation_cert_required,
        self_attestation_permitted,
        none_attestation_permitted,
        uv_required=False)  # User Verification

    try:
        webauthn_credential = webauthn_registration_response.verify()
    except Exception as e:
        return jsonify({'fail': 'Registration failed. Error: {}'.format(e)})

    # Step 17.
    #
    # Check that the credentialId is not yet registered to any other user.
    # If registration is requested for a credential that is already registered
    # to a different user, the Relying Party SHOULD fail this registration
    # ceremony, or it MAY decide to accept the registration, e.g. while deleting
    # the older registration.
    # TODO: replace with future stored proc
    dbcursor.execute('SELECT credential_id FROM test WHERE credential_id = %s', (webauthn_credential.credential_id,))
    credential_id_exists = dbcursor.fetchone()
    
    if credential_id_exists:
        return make_response(
            jsonify({
                'fail': 'Credential ID already exists.'
            }), 401)

    #dbcursor.execute('SELECT email FROM test WHERE email = %s', (email,))
    #existing_user = dbcursor.fetchone()
    #if not existing_user:
    dbcursor.callproc('user_select_users', args=(email,))
    if not get_first_result(dbcursor):
        if sys.version_info >= (3, 0):
            webauthn_credential.credential_id = str(
                webauthn_credential.credential_id, "utf-8")
            webauthn_credential.public_key = str(
                webauthn_credential.public_key, "utf-8")
        '''
        user = User(
            ukey=ukey,
            username=username,
            display_name=display_name,
            pub_key=webauthn_credential.public_key,
            credential_id=webauthn_credential.credential_id,
            sign_count=webauthn_credential.sign_count,
            rp_id=RP_ID,
            icon_url='https://example.com')
        db.session.add(user)
        db.session.commit()
        '''
        # Add new user entry to database table (TODO: replace with future stored proc)
        dbcursor.execute('INSERT INTO users (email, display_name, ukey, icon_url, credential_id, pub_key, sign_count, rp_id) VALUES (%s, %s, %s, %s, %s, %s, %d, %s)', (email, display_name, ukey, 'https://example.com', webauthn_credential.credential_id, webauthn_credential.public_key, webauthn_credential.sign_count, RP_ID))
        dbconnection.commit()
    else:
        return make_response(jsonify({'fail': 'User already exists.'}), 401)

    #flash('Successfully registered with email {}.'.format(email))

    return jsonify({'success': 'User successfully registered.'})


@app.route('/verify_assertion', methods=['POST'])
def verify_assertion():
    challenge = session.get('challenge')
    assertion_response = request.form
    credential_id = assertion_response.get('id')

    # TODO: replace with future stored proc
    dbcursor.execute('SELECT email, display_name, ukey, icon_url, credential_id, pub_key, sign_count, rp_id FROM test WHERE credential_id = %s', (credential_id,))
    user = dbcursor.fetchone()
    if not user:
        return make_response(jsonify({'fail': 'User does not exist.'}), 401)

    webauthn_user = webauthn.WebAuthnUser(
        user[2], # user.ukey
        user[0], # user.username or email in our case
        user[1], # user.display_name
        user[3], # user.icon_url
        user[4], # user.credential_id
        user[5], # user.pub_key
        user[6], # user.sign_count
        user[7]) # user.rp_id

    webauthn_assertion_response = webauthn.WebAuthnAssertionResponse(
        webauthn_user,
        assertion_response,
        challenge,
        ORIGIN,
        uv_required=False)  # User Verification

    try:
        sign_count = webauthn_assertion_response.verify()
    except Exception as e:
        return jsonify({'fail': 'Assertion failed. Error: {}'.format(e)})

    # Update counter.
    user.sign_count = sign_count
    # TODO: replace with future stored proc
    dbcursor.execute('INSERT INTO users (email, display_name, ukey, icon_url, credential_id, pub_key, sign_count, rp_id) VALUES (%s, %s, %s, %s, %s, %s, %d, %s)', (user[0], user[1], user[2], user[3], user[4], user[5], user[6], user[7]))
    dbconnection.commit()

    # TODO: find an equivalent for login_manager
    #login_user(user)

    return jsonify({
        'success':
        'Successfully authenticated as {}'.format(user[0])
    })

@app.route('/webauthn_login', methods=['GET', 'POST'])
def webauthn_login():
     # If user enters form data and session cookie has no record of username:
    if request.method == 'POST':
        # Query database for provided username
        #dbcursor.execute('SELECT email, pass FROM test WHERE email = %s', (request.form['email'],))
        dbcursor.callproc('email_fetch_user', args=(request.form['email'],))
        # Save query result (tuple if found, `None` otherwise)
        #result = dbcursor.fetchone()
        stored_email, stored_password = get_first_result(dbcursor) or (None, None)
        # Verify provided password
        pw_hash = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        #if result and bcrypt.check_password_hash(pw_hash, result[1]):
        if stored_password and bcrypt.check_password_hash(pw_hash, stored_password):
            #For making this easier to check, ## will signify what is in routes.py
            ## Save username as validation of login
            ##session['username'] = result[0]

            login_user(user) #logs in the user and automatically stores user's ID in session

            flask.flash('Logged in Successfully')

            # I don't know if we will need to check if the url is safe for redirects, here is the code
            #next = flask.request.args.get('next')

            #if not is_safe_url(next):
                #return flask.abort(400)


            # Redirect user to profile page (back to login page for now)
            return redirect(url_for('login'))
    # Display home page
    return render_template('index.html')



@app.route('/webauthn_logout')
@login_required
def webauthn_logout():
    logout_user()
    return redirect(url_for('index'))

