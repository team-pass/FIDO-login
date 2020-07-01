''' API ROUTE IMPLEMENTATION '''
from flask import request, session, render_template, url_for, redirect
from . import app, bcrypt, dbconnection, dbcursor


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def login():
    # If user enters form data and session cookie has no record of email:
    if request.method == 'POST' and 'email' not in session:
        # Query database for provided email
        dbcursor.execute(
            'SELECT email, pass FROM test WHERE email = %s', (request.form['email'],)
        )
        # Save query result (tuple if found, `None` otherwise)
        result = dbcursor.fetchone()
        # Verify provided password
        pw_hash = bcrypt.generate_password_hash(request.form['password']).decode(
            'utf-8'
        )
        if result and bcrypt.check_password_hash(pw_hash, result[1]):
            # Save email as validation of login
            session['email'] = result[0]
            # Redirect user to profile page
            return redirect(url_for('profile'))
    # Display home page
    return render_template('index.html')


# PLACEHOLDER---currently no way to reach this without manual URL entry
@app.route('/logout')
def logout():
    # Remove record of email in session cookie
    session.pop('email', None)
    # Redirect user to login page
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    # If user enters form data and session cookie has no record of email:
    if request.method == 'POST' and 'email' not in session:
        # Proceed if provided email is not already taken
        email = request.form['email']
        dbcursor.execute('SELECT email FROM test WHERE email = %s', (email,))
        if not dbcursor.fetchone():
            # Get plaintext of provided password
            password = request.form['password']
            # Encrypt and convert to String
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            # Add new user entry to database table
            dbcursor.execute(
                'INSERT INTO test (email, pass) VALUES (%s, %s)',
                (email, hashed_password),
            )
            dbconnection.commit()
            # Redirect user to login page
            return redirect(url_for('login'))
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
    return render_template('profile.html', favorite_number)
