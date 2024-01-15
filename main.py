# main.py

import threading
from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    render_template_string,
)
from flask_login import login_required, current_user
import tidalapi

from database import add_tidal_user_token


def login_thread(user_id, future, tidal_session):
    # Warten Sie, bis der Benutzer sich angemeldet hat
    future.result()

    # Überprüfen Sie, ob der Benutzer angemeldet ist
    if tidal_session.check_login() is False:
        # flash("Der Benutzer hat sich nicht angemeldet")
        print("Der Benutzer mit der id " + str(user_id) + " hat sich nicht angemeldet")
        return

    # Speichern Sie den Token in der Datenbank
    add_tidal_user_token(
        user_id,
        {
            "token_type": tidal_session.token_type,
            "access_token": tidal_session.access_token,
            "refresh_token": tidal_session.refresh_token,
            "expiry_time": tidal_session.expiry_time,
        },
    )

    print(
        "Der Benutzer mit der id "
        + str(user_id)
        + " hat sich erfolgreich bei TIDAL angemeldet"
    )


main = Blueprint("main", __name__)


@main.after_request  # Wird nach jedem Aufruf in main ausgeführt
def start_thread(response):
    if request.endpoint == "main.login_tidal":
        thread = threading.Thread(
            target=login_thread,
            args=(current_user.id, current_user.future, current_user.tidal_session),
        )
        thread.start()
    return response


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/profile")
@login_required
def profile():
    if current_user.tidal_session is None:
        return render_template("profile.html")

    tidal_expires_in = (
        current_user.tidal_session.expiry_time - datetime.now().timestamp()
    )

    return render_template("profile.html", tidal_expires_in=tidal_expires_in)


@main.route("/login/tidal")
@login_required
def login_tidal():
    if current_user.tidal_session is not None:
        flash(
            "Es existiert bereits eine TIDAL-Session"
        )  # BUG: flash muss in main.profile implementiert werden
        return redirect(url_for("main.profile"))

    current_user.set_tidal_session(tidalapi.Session())
    login, future = current_user.get_tidal_session().login_oauth()

    current_user.future = future

    return redirect("https://link.tidal.com/" + login.user_code)
