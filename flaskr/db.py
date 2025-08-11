import sqlite3
import click
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash
import logging

def get_db():
    """Get a database connection, or create one if it doesn't exist."""
    if 'db' not in g:
        try:
            g.db = sqlite3.connect(
                current_app.config['DATABASE'],
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            g.db.row_factory = sqlite3.Row  # Access rows as dictionaries
            logging.debug("Database connection established.")
        except sqlite3.Error as e:
            logging.error("Database connection failed: %s", str(e))
            raise
    else:
        logging.debug("Using existing database connection.")

    return g.db

def close_db(e=None):
    """Close the database connection if it exists."""
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
            logging.debug("Database connection closed.")
        except sqlite3.Error as e:
            logging.error("Failed to close database connection: %s", str(e))

def init_db():
    """Initialize the database schema."""
    try:
        db = get_db()
        with current_app.open_resource('schema.sql') as f:
            db.executescript(f.read().decode('utf8'))
        logging.info("Database schema initialized successfully.")
    except FileNotFoundError:
        logging.error("Schema file not found during initialization.")
        raise
    except sqlite3.Error as e:
        logging.error("Error initializing database schema: %s", str(e))
        raise

@click.command('init-db')
@with_appcontext
def init_db_command():
    """CLI command to initialize the database."""
    try:
        init_db()
        click.echo('Initialized the database.')
        logging.info("Database initialization command executed successfully.")
    except Exception as e:
        click.echo(f'Error initializing database: {str(e)}')
        logging.error("Database initialization failed: %s", str(e))

@click.command('init-moderator')
@click.argument('email')
@click.argument('nickname')
@click.argument('password')
@with_appcontext
def init_moderator_command(email, nickname, password):
    """CLI command to create a default moderator."""
    logging.debug("Attempting to create moderator with email %s.", email)
    db = get_db()
    try:
        db.execute(
            'INSERT INTO user (email, nickname, password, role) VALUES (?, ?, ?, ?)',
            (email, nickname, generate_password_hash(password), 'Moderator')
        )
        db.commit()
        click.echo('Moderator created successfully!')
        logging.info("Moderator %s created successfully with email %s.", nickname, email)
    except sqlite3.IntegrityError as e:
        click.echo(f'Error: {str(e)}')
        logging.error("Failed to create moderator with email %s: %s", email, str(e))
    except sqlite3.Error as e:
        click.echo(f'Error: {str(e)}')
        logging.error("Unexpected database error while creating moderator: %s", str(e))

def init_app(app):
    """Initialize the app with teardown and CLI commands."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(init_moderator_command)
    logging.info("App initialized with DB teardown and CLI commands.")
