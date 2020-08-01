''' API ROUTE IMPLEMENTATION '''
from flask import request, session, render_template, url_for, redirect, flash
from . import app, bcrypt, dbconnection, dbcursor, log
import mysql
from .utils import get_first_result
from random import randint


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect the user to the profile page if they're already logged in
    if 'email' in session:
        return redirect(url_for('profile'))

    # Return the login template if the user is just GETTING the page
    if request.method == 'GET':
        return render_template('login.html')

    # Otherwise, it's a post request
    email = request.form.get('email')
    password = request.form.get('password')

    # Ensure all required fields
    if not (email and password):
        flash('Must enter a username and password', 'error')
        return redirect(url_for('login'))

    # Check that a user has a matching email/password combo
    dbcursor.callproc('email_fetch_user', args=(email,))
    stored_email, stored_password = get_first_result(dbcursor) or (None, None)

    # If the user's password is incorrect, let them know
    log('stored_password type: ' + str(type(stored_password)))
    log('password type: ' + str(type(password)))
    if not bcrypt.check_password_hash(stored_password, password):
        flash('Username or passsword is incorrect', 'error')
        return redirect(url_for('login'))

    # Log the user into the profile page
    session['email'] = stored_email
    return redirect(url_for('profile'))


@app.route('/logout', methods=['POST'])
def logout():
    # Remove record of email in session cookie before redirection
    session.pop('email', None)
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    # Redirect the user to the profile page if they're already logged in
    if 'email' in session:
        return redirect(url_for('profile'))

    # Serve the page on a GET request
    if request.method == 'GET':
        return render_template('register.html')

    # Otherwise, handle the POST request to register a new user account
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    # Ensure the user entered all correct information
    if not (email and password and confirm_password):
        flash('Missing required fields', 'error')
        return redirect(url_for('register'))

    # Ensure the passwords match
    if password != confirm_password:
        flash('Passwords did not match', 'error')
        return redirect(url_for('register'))

    # Ensure the user's email isn't already in use
    dbcursor.callproc('user_select_users', args=(email,))
    if get_first_result(dbcursor):
        flash('Email address is already in use', 'error')
        return redirect(url_for('register'))

    # Add new user entry to database table
    username = email
    favorite_number = randint(0, 100)
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # TODO: fix this to only use email, password, & favorite number!
    dbcursor.callproc(
        'register_user', args=(username, hashed_password, email, favorite_number),
    )

    # Redirect user to login page
    flash('Registered your account successfully!', 'message')
    return redirect(url_for('login'))


# Page to edit user information
@app.route('/profile')
def profile():
    # A user must be logged in to view their profile
    if 'email' not in session:
        return redirect(url_for('login'))

    # If the user's favorite number isn't set, default to the string "??"
    # TODO: implement this call as a stored procedure
    # dbcursor.execute(
    #     'SELECT favorite_number FROM test WHERE email = %s LIMIT 1', (session["email"],)
    # )
    favorite_number = dbcursor.fetchone() or "??"

    # Pass the favorite_number variable to the profile template
    return render_template('profile.html', favorite_number=favorite_number)
