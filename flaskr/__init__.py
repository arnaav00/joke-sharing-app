import os
import logging
from logging.handlers import RotatingFileHandler
from . import db
from flask import Flask, redirect, url_for, session, g, current_app, request
from . import auth
from . import jokes
from . import moderation
import click
from flask.cli import with_appcontext

def setup_logging(app=None):
    # Ensure logs directory exists
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # Format for log entries
    log_format = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')

    # Create a rotating file handler for the log file
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB per log file
        backupCount=5  # Keep 5 backup logs
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.INFO)  # Default to INFO level for log file

    # Create console handler for console output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.WARN)  # Default to WARN level for console

    # Get the root logger and add handlers
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Default to INFO for the root logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Modify log level based on app configuration
    if app and app.config.get('DEBUG_LOGGING', False):
        logger.setLevel(logging.DEBUG)
        file_handler.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.DEBUG)


def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )
    app.config['DEBUG'] = True  # Set for local debugging
    logging.info("Program start. Flask app configured with SECRET_KEY and DATABASE.")

    if test_config is None:
        # Load instance config if not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load test config
        app.config.from_mapping(test_config)
    
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError as e:
        logging.critical("Instance folder creation failed: %s", e)
        raise

    setup_logging(app)
    logging.info("Logging setup complete.")
    
    db.init_app(app)
    logging.info("Database initialized.")
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(jokes.bp)
    app.register_blueprint(moderation.bp)
    logging.info("Blueprints registered: auth, jokes, moderation.")

    @app.before_request
    def before_request():
        logging.debug("Before request processing started.")
        g.user = None  # Initialize g.user
        g.session_id = request.cookies.get('session', 'Unknown')
        logging.debug("Processing session ID: %s", g.session_id)

        if 'user_id' in session:
            user_id = session['user_id']
            connection = db.get_db()

            try:
                user_data = connection.execute(
                    'SELECT * FROM user WHERE id = ?', (user_id,)
                ).fetchone()
                logging.debug("Query result for user_id %d: %s", user_id, user_data)

                if user_data:
                    g.user = user_data
                    g.role = user_data['role']
                    g.joke_balance = user_data['joke_balance']
                    logging.info("User session initialized: user_id=%d, role=%s", user_id, g.role)
                else:
                    session.clear()
                    logging.warning("Invalid user_id in session; session cleared.")
            except Exception as e:
                logging.error("Error during user session initialization: %s", e)
                session.clear()
        else:
            g.role = 'user'
            g.joke_balance = 0
            logging.debug("Default role and joke balance assigned.")

    @app.after_request
    def after_request(response):
        logging.info("Response returned with status code %d for %s %s", response.status_code, request.method, request.path)
        if response.status_code >= 400:
            logging.warning("Non-successful HTTP response: %d", response.status_code)
        return response

    @app.route('/')
    def index():
        logging.info("Redirecting to login page.")
        return redirect(url_for('auth.login'))
    
    # CLI command to toggle debug mode
    @click.command('toggle-debug')
    @click.argument('mode', type=click.Choice(['on', 'off']))
    @with_appcontext
    def toggle_debug_command(mode):
        app.debug = True if mode == 'on' else False
        app.config['DEBUG_LOGGING'] = (mode == 'on')
        logging.info("Debug mode toggled to %s", mode)
        click.echo(f"Debug mode set to {mode}")

    # Register the CLI command
    app.cli.add_command(toggle_debug_command)

    logging.info("App creation complete.")
    return app
