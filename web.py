from flask import Flask, render_template, request, redirect, url_for
from flask_login import (
    LoginManager,
    login_user as login_user_flask,
    login_required as login_required_flask,
    logout_user as logout_user_flask,
    current_user,
)

import re

from database import (
    init_database,
    signup_user as signup_user_db,
    login_user as login_user_db,
    get_user_by_id as get_user_by_id_db,
)

from user import User

app = Flask(__name__, template_folder="web")
app.secret_key = "CvyZWUaNANYc8SbwsMTxAwoNMyRVM2"

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id_db(user_id)


@login_manager.unauthorized_handler
def unauthorized():
    # Wenn der Benutzer nicht eingeloggt ist, wird er auf die Login-Seite weitergeleitet
    return redirect(url_for("login"))


# TODO: Startseite implementieren, dabei Loginstatus berücksichtigen
@app.route("/")
@login_required_flask
def index():
    return render_template("index.html", user=current_user, error=None)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # TODO: Testfälle testen
        if len(password) < 8:
            error = "Das Passwort muss mindestens 8 Zeichen lang sein."
            return render_template("signup.html", error=error)
        if len(email) > 255:
            error = "E-Mail-Adresse darf maximal 255 Zeichen lang sein."
            return render_template("signup.html", error=error)
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            error = "E-Mail-Adresse ist ungültig."
            return render_template("signup.html", error=error)
        if email == "":
            error = "E-Mail-Adresse darf nicht leer sein."
            return render_template("signup.html", error=error)
        if password == "":
            error = "Passwort darf nicht leer sein."
            return render_template("signup.html", error=error)

        # Versuche, den Benutzer anzulegen, falls über die Datenbank ein Fehler erkannt wird,
        # wird eine Exception geworfen, die hier abgefangen und als Fehlermeldung angezeigt wird.
        try:
            user = signup_user_db(email, password)
            login_user_flask(user)
            return redirect(url_for("index"))
        except Exception as e:
            return render_template("signup.html", error=str(e))
    elif request.method == "GET":
        return render_template("signup.html", error=None)


@app.route("/login", methods=["GET", "POST"])
def login():
    # Wenn error nicht auf None gesetzt wird, wird die Fehlermeldung angezeigt,
    # auch beim nächsten Aufruf der Seite
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # TODO: Testfälle testen
        if len(password) < 8:
            error = "Das Passwort muss mindestens 8 Zeichen lang sein."
            return render_template("login.html", error=error)
        if email == "":
            error = "E-Mail-Adresse darf nicht leer sein."
            return render_template("login.html", error=error)
        if password == "":
            error = "Passwort darf nicht leer sein."
            return render_template("login.html", error=error)

        # Versuche, den Benutzer einzuloggen, falls über die Datenbank ein Fehler erkannt wird,
        # wird eine Exception geworfen, die hier abgefangen und als Fehlermeldung angezeigt wird.
        try:
            user = login_user_db(email, password)
            login_user_flask(user)
            return redirect(url_for("index"))
        except Exception as e:
            return render_template("login.html", error=str(e))
    elif request.method == "GET":
        return render_template("login.html", error=None)


@app.route("/logout")
@login_required_flask
def logout():
    logout_user_flask()
    return redirect(url_for("logout_success"))


@app.route("/logout-success")
def logout_success():
    return render_template("logout_success.html")


if __name__ == "__main__":
    init_database()
    app.run(host="0.0.0.0", port=3000, debug=True)
