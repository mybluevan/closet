"""
    Closet
    ~~~~~~

    A personal clothing catalog written with Flask.

    :copyright: (c) 2015 by David Nichols.
"""

# all the imports
import sqlite3
from contextlib import closing
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash

# create application
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'closet.db'),
    DEBUG=True,
    SECRET_KEY='bug off',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

def connect_db():
    """Connects to the database."""
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    """Initializes the database."""
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    db = getattr(g, 'db', None)
    if db is None:
        db = g._database = connect_to_database()
    return db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the app/request."""
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()
