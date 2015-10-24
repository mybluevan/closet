import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from closet import app, get_db


@app.route('/')
def show_garments():
    db = get_db()
    cur = db.execute('select description from garments order by id desc')
    garments = [dict(description=row[0]) for row in cur.fetchall()]
    return render_template('show_garments.html', garments=garments)


@app.route('/add', methods=['POST'])
def add_garment():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into garments (description) values (?)',
               [request.form['description'], ])
    db.commit()
    flash('New garment was successfully added', 'success')
    return redirect(url_for('show_garments'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            flash('Invalid username', 'warning')
        elif request.form['password'] != app.config['PASSWORD']:
            flash('Invalid password', 'warning')
        else:
            session['logged_in'] = True
            flash('You were logged in', 'success')
            return redirect(url_for('show_garments'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out', 'info')
    return redirect(url_for('show_garments'))
