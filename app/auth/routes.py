from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import (
    login_user,
    login_required,
    logout_user,
    current_user,
)
from sqlalchemy.exc import IntegrityError
from email_validator import validate_email, EmailNotValidError

from app.models.user import User
from app.extensions import db
from app.auth import bp


@bp.route("/signup", methods=["GET"])
def signup():
    return render_template("signup.html")


@bp.route("/signup", methods=["POST"])
def signup_post():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    # TODO: Testfälle überarbeiten
    if len(password) < 8:
        flash("Das Passwort muss mindestens 8 Zeichen lang sein.")
        return redirect(url_for("auth.signup"))
    if password == "":
        flash("Passwort darf nicht leer sein.")
        return redirect(url_for("auth.signup"))

    # E-Mail-Adresse validieren
    try:
        emailinfo = validate_email(email, check_deliverability=False)
        email = emailinfo.normalized
    except EmailNotValidError as e:
        flash("E-Mail-Adresse ist ungültig.")
        print(str(e))
        return redirect(url_for("auth.signup"))

    # Versuche, den Benutzer anzulegen, falls über die Datenbank ein Fehler erkannt wird,
    # wird eine Exception geworfen, die hier abgefangen und als Fehlermeldung angezeigt wird.
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.commit()
        # Benutzer erfolgreich angelegt
    except IntegrityError:
        # Eindeutiger Schlüsselverstoß, Benutzer konnte nicht angelegt werden
        flash("E-Mail-Adresse oder Benutzername bereits vergeben.")
        return redirect(url_for("auth.signup"))

    # Nachdem der Benutzer angelegt wurde, wird er eingeloggt und zur Startseite weitergeleitet
    login_user(user, remember=True)
    return redirect(url_for("main.index"))


@bp.route("/login", methods=["GET"])
def login():
    return render_template("login.html")


@bp.route("/login", methods=["POST"])
def login_post():
    # Wenn error nicht auf None gesetzt wird, wird die Fehlermeldung angezeigt,
    # auch beim nächsten Aufruf der Seite
    email = request.form.get("email")
    password = request.form.get("password")
    remember = True if request.form.get("remember") else False

    # TODO: Testfälle testen
    if len(password) < 8:
        flash("Das Passwort muss mindestens 8 Zeichen lang sein.")
        return redirect(url_for("auth.login"))
    if email == "":
        flash("E-Mail-Adresse darf nicht leer sein.")
        return redirect(url_for("auth.login"))
    if password == "":
        flash("Passwort darf nicht leer sein.")
        return redirect(url_for("auth.login"))

    # Versuche, den Benutzer einzuloggen, falls über die Datenbank ein Fehler erkannt wird,
    # wird eine Exception geworfen, die hier abgefangen und als Fehlermeldung angezeigt wird.
    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        # Benutzer konnte nicht gefunden werden oder Passwort ist falsch
        flash("E-Mail-Adresse oder Passwort falsch.")
        return redirect(url_for("auth.login"))
    else:
        login_user(user, remember=remember)
        return redirect(url_for("main.index"))


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return render_template("logout_success.html")
