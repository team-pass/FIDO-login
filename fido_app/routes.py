''' API ROUTE IMPLEMENTATION '''

from flask import request, session, render_template, url_for, redirect, flash
from flask_login import current_user, login_user, logout_user, login_required
from . import app, login_manager, db
from .utils import validate_email, get_display_name
from .models import User


@login_manager.user_loader
def load_user(user_id):
    """Loads a user based on their id, returning None if they don't exist"""
    return User.query.get(int(user_id))


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    # Return the login template if the user is just GETTING the page
    if request.method == 'GET':
        return render_template('login.html')

    # Otherwise, it's a post request
    email = request.form.get('email')
    password = request.form.get('password')

    # Ensure all required fields
    if not (email and password):
        flash('Must enter an email and a password', 'error')
        return redirect(url_for('login'))

    # Check that a user has a matching email/password combo
    user = User.query.filter_by(email=email).first()

    # If the user's password is incorrect, let them know
    if not user or not user.check_password(password):
        flash('Email or passsword is incorrect', 'error')
        return redirect(url_for('login'))

    # Log the user into the profile page
    login_user(user, remember=True)
    return redirect(url_for('profile'))


@app.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    # Serve the page on a GET request
    if request.method == 'GET':
        return render_template('register.html')

    # Otherwise, handle the POST request to register a new user account
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm-password')

    # Ensure the user entered all correct information
    if not (email and password and confirm_password):
        flash('Missing required fields', 'error')
        return redirect(url_for('register'))

    # Ensure the passwords match
    if password != confirm_password:
        flash('Passwords did not match', 'error')
        return redirect(url_for('register'))

    # Ensure the email is valid
    if not validate_email(email):
        flash('Invalid email address', 'error')
        return redirect(url_for('register'))

    # Ensure the user's email isn't already in use
    if User.query.filter_by(email=email).first():
        flash('Email address is already in use', 'error')
        return redirect(url_for('register'))

    # Add new user entry to database
    new_user = User(
        email=email,
        display_name=get_display_name(email),
        icon_url='https://example.com',
    )
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    # Redirect user to login page
    flash(f'Successfully registered with email {email}')
    return redirect(url_for('login'))


# Page to edit user information
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@app.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    email = current_user.email

    # Delete the user in the database and log them out
    User.query.filter_by(id=current_user.id).delete()
    logout_user()
    db.session.commit()

    flash(f'Successfully deleted the account for "{email}"', 'message')
    return redirect(url_for('login'))
