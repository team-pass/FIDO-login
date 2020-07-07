''' API ROUTE IMPLEMENTATION '''
from flask import request, session, render_template, url_for, redirect, flash
from . import app, bcrypt, dbconnection, dbcursor


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect the user to the profile page if they're already logged in
    if 'email' in session:
        return redirect(url_for('profile'))

    # If user enters form data and session cookie has no record of email:
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if email and password:
            # Check that a user has a matching email/password combo
            dbcursor.execute(
                'SELECT email, pass FROM test WHERE email = %s', (email,),
            )
            result = dbcursor.fetchone()
            pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')

            if result and bcrypt.check_password_hash(pw_hash, result[1]):
                # Save email as validation of login and redirect to the profile page
                session['email'] = result[0]
                return redirect(url_for('profile'))
            else:
                # If the user's info is incorrect, let them know
                flash('Username or passsword is incorrect.', 'error')
        else:
            flash('Must enter a username and password.', 'error')

        # Prevent refreshing the page from resubmitting the form
        return redirect(url_for('login'))

    # Display home page
    return render_template('login.html')


# PLACEHOLDER---currently no way to reach this without manual URL entry
@app.route('/logout')
def logout():
    # Remove record of email in session cookie
    session.pop('email', None)
    # Redirect user to login page
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    # Redirect the user to the profile page if they're already logged in
    if 'email' in session:
        return redirect(url_for('profile'))

    # If user enters form data and session cookie has no record of email:
    if request.method == 'POST':
        # Proceed if provided email is not already taken
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # If the user entered all correct information
        if email and password and confirm_password:
            # Make sure the passwords the user put in match
            if password == confirm_password:
                dbcursor.execute('SELECT email FROM test WHERE email = %s', (email,))
                if not dbcursor.fetchone():
                    # Encrypt and convert to String
                    hashed_password = bcrypt.generate_password_hash(password).decode(
                        'utf-8'
                    )
                    # Add new user entry to database table
                    # dbcursor.execute(
                    #     'INSERT INTO test (email, pass) VALUES (%s, %s)',
                    #     (email, hashed_password),
                    # )
                    # dbconnection.commit()
                    flash('Registered your account successfully!', 'message')

                    # Redirect user to login page
                    return redirect(url_for('login'))
                else:
                    flash('Email is already in use.', 'error')
            else:
                flash('Passwords did not match.', 'error')
        else:
            flash('Missing required fields.', 'error')

        # Prevent refreshing the page from resubmitting the form
        return redirect(url_for('register'))

    # Display registration page
    return render_template('register.html')


# Page to edit user information
@app.route('/profile')
def profile():
    if "email" not in session:
        return redirect(url_for('login'))

    dbcursor.execute(
        'SELECT favorite_number FROM test WHERE email = %s', (session["email"],)
    )

    # If the user's favorite number isn't set, default to the string "??"
    favorite_number = dbcursor.fetchone() or "??"

    # Pass the favorite_number variable to the profile template
    return render_template('profile.html', favorite_number=favorite_number)
