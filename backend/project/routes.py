#### ROUTING IMPLEMENTATION ####


from flask import request, session, render_template, url_for
from project import app, bcrypt, dbconnection, dbcursor


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def login():
    # If user enters form data and session cookie has no record of username:
    if request.method == 'POST' and 'username' not in session:
        # Query database for provided username
        dbcursor.execute('SELECT username, password FROM users WHERE username = %s', (request.form['username'],))
        # Save query result (tuple if found, `None` otherwise)
        result = dbcursor.fetchone()
        # Verify provided password
        if result and bcrypt.check_password_hash(result, request.form['password']):
            # Save username as validation of login
            session['username'] = result[0]
            # Redirect user to profile page (back to login page for now)
            return redirect(url_for('login'))
    # Display home page
    return render_template('index.html')


# PLACEHOLDER---currently no way to reach this without manual URL entry
@app.route('/logout')
def logout():
    # Remove record of username in session cookie
    session.pop('username', None)
    # Redirect user to login page
    return redirect(url_for('login'))


@app.route('/registration', methods=['GET', 'POST'])
def register():    
    # If user enters form data and session cookie has no record of username:
    if request.method == 'POST' and 'username' not in session:
        # Proceed if provided username is not already taken
        username = request.form['username']
        dbcursor.execute('SELECT username FROM users WHERE username = %s', (username,))
        if not dbcursor.fetchone():
            # Get plaintext of provided password
            password = request.form['password']
            # Encrypt and convert to String
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            # Add new user entry to database table
            dbcursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, hashed_password))
            dbconnection.commit()
            # Redirect user to login page
            return redirect(url_for('login'))
    # Display registration page
    return render_template('registration.html')


# PLACEHOLDER---page doesn't exist as of now
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')
