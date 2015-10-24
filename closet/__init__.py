"""
    Closet
    ~~~~~~

    A personal clothing catalog written with Flask.

    :copyright: (c) 2015 by David Nichols.
"""

# all the imports
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from flask.ext.script import Manager

# create application
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'closet.db'),
    DEBUG=False,
    SECRET_KEY='bug off',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('CLOSET_SETTINGS', silent=True)

manager = Manager(app)


@manager.command
def init_db():
    """Initializes the database."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
    print("Database initialized.")


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    db = getattr(g, 'db', None)
    if db is None:
        db = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
        g.db = db
    return db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the app/request."""
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

import closet.views
