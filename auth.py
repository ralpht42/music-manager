# auth.py

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import (
    login_user as login_user_flask,
    login_required as login_required_flask,
    logout_user as logout_user_flask,
    current_user,
)

from models import User

import re

from database import (
    init_database,
    signup_user as signup_user_db,
    login_user as login_user_db,
    get_user_by_id as get_user_by_id_db,
)  


auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    # TODO: Testfälle testen
    if len(password) < 8:
        flash("Das Passwort muss mindestens 8 Zeichen lang sein.")
        return redirect(url_for('auth.login'))
    if email == "":
        flash("E-Mail-Adresse darf nicht leer sein.")
        return redirect(url_for('auth.login'))
    if password == "":
        flash("Passwort darf nicht leer sein.")
        return redirect(url_for('auth.login'))


    try:
        user = login_user_db(email, password)
        if not user:
            raise Exception("E-Mail-Adresse oder Passwort ist falsch")
        login_user_flask(user, remember=remember)
        return redirect(url_for('main.profile'))
    except Exception as e:
        flash(str(e))
        return redirect(url_for('auth.login'))

@auth.route('/signup')
def signup():
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():

    email = request.form.get('email')
    username = request.form.get('username')
    password = request.form.get('password')

    # TODO: Testfälle testen
    if len(password) < 8:
        flash("Das Passwort muss mindestens 8 Zeichen lang sein.")
        return redirect(url_for('auth.signup'))
    if len(email) > 255:
        flash("Die E-Mail-Adresse darf maximal 255 Zeichen lang sein.")
        return redirect(url_for('auth.signup'))
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        flash("Die E-Mail-Adresse ist ungültig.")
        return redirect(url_for('auth.signup'))
    if email == "":
        flash("E-Mail-Adresse darf nicht leer sein.")
        return redirect(url_for('auth.signup'))
    if password == "":
        flash("Passwort darf nicht leer sein.")
        return redirect(url_for('auth.signup'))

    try:
        user = signup_user_db(username, email, password)
    except Exception as e:
        flash(str(e))
        return redirect(url_for('auth.signup'))

    return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required_flask
def logout():
    logout_user_flask()
    return redirect(url_for('main.index'))