import logging
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from .db import get_db
from functools import wraps

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            logging.warning("Unauthorized access attempt, redirecting to login.")
            return redirect(url_for('auth.login'))
        logging.debug("User ID %s authorized for access.", session['user_id'])
        return f(*args, **kwargs)
    return decorated_function

# Role required decorator
def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] != role:
                logging.warning("Authorization failure for role %s, redirecting to login.", session.get('role', 'guest'))
                flash('You do not have the required permissions to access this page.', 'danger')
                return redirect(url_for('auth.login'))
            logging.debug("User with role %s authorized for access.", session['role'])
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@bp.before_app_request
def load_logged_in_user():
    """Ensure g.user is updated with logged-in user details for every request."""
    user_id = session.get('user_id')
    if user_id:
        logging.debug("Fetching user data for user ID %s.", user_id)
        user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()
        if user:
            g.user = user
            g.role = user['role']
            g.joke_balance = user['joke_balance']
            logging.info("User ID %s loaded into g context with role %s.", user_id, g.role)
        else:
            logging.error("User ID %s in session does not exist in the database.", user_id)
            session.clear()
            g.user = None
    else:
        g.user = None
        logging.debug("No user logged in during request.")

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        logging.debug("Login attempt with username/email: %s", username)
        db = get_db()
        user = db.execute(
            'SELECT * FROM user WHERE nickname = ? OR email = ?',
            (username, username)
        ).fetchone()

        if user and check_password_hash(user['password'], password):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['nickname']
            session['role'] = user['role']  # Store the user role in session
            logging.info("User %s logged in successfully with role %s.", user['nickname'], user['role'])
            return redirect(url_for('jokes.leave'))

        flash('Invalid username or password', 'danger')
        logging.warning("Failed login attempt for username/email: %s.", username)

    logging.debug("Rendering login page.")
    return render_template('auth/login.html')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        email = request.form['email']
        nickname = request.form['nickname']
        password = request.form['password']
        logging.debug("Registration attempt with email: %s and nickname: %s", email, nickname)
        db = get_db()
        try:
            db.execute(
                'INSERT INTO user (email, nickname, password, role) VALUES (?, ?, ?, ?)',
                (email, nickname, generate_password_hash(password), 'User')  # Default role is 'user'
            )
            db.commit()
            flash('Registration successful, please log in.', 'success')
            logging.info("User %s registered successfully with email %s.", nickname, email)
            return redirect(url_for('auth.login'))
        except db.IntegrityError:
            flash('Email or Nickname already exists. Please choose a different one.', 'danger')
            logging.error("Registration failed: Email or nickname already exists for %s.", email)

    logging.debug("Rendering registration page.")
    return render_template('auth/register.html')

@bp.route('/logout')
def logout():
    user_id = session.get('user_id', 'Unknown')
    username = session.get('username', 'Unknown')
    session.clear()
    logging.info("User ID %s (%s) logged out.", user_id, username)
    return redirect(url_for('auth.login'))
