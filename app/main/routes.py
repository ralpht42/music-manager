import threading
from datetime import datetime

from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
    render_template_string,
    current_app,
)
from flask_login import login_required, current_user
import tidalapi

from app.main import bp
from app.models.user import User, TidalAccount

from app.extensions import db


def login_thread(app, user):
    # Lade die Variablen aus dem User-Objekt
    user_id = user.get_id()
    tidal_future = user.get_tidal_future()
    tidal_session = user.get_tidal_session()


    # Warten Sie, bis der Benutzer sich angemeldet hat
    tidal_future.result()

    with app.app_context():
        tidal_account = TidalAccount.query.filter_by(id=user.tidal_account_id).first()
        if tidal_account is None:
            tidal_account = (
                TidalAccount()
            )  # Wenn kein Account existiert, wird ein neuer erstellt

        tidal_account.access_token = tidal_session.access_token
        tidal_account.refresh_token = tidal_session.refresh_token
        tidal_account.expiry_time = tidal_session.expiry_time

        db.session.add(tidal_account)
        db.session.commit()

        user = User.query.filter_by(id=user_id).first()
        # Verknüpfung kann redundant sein, falls tidal_account bereits in der Datenbank existierte
        user.tidal_account_id = tidal_account.id
        db.session.add(user)
        db.session.commit()


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/profile")
@login_required
def profile():
    if current_user.tidal_session is None:
        return render_template("profile.html")

    tidal_expires_in = (
        current_user.tidal_session.expiry_time.timestamp() - datetime.now().timestamp()
    )

    return render_template("profile.html", tidal_expires_in=tidal_expires_in)


@bp.route("/login/tidal")
@login_required
def login_tidal():
    if current_user.tidal_session is not None:
        flash(
            "Es existiert bereits eine TIDAL-Session"
        )  # BUG: flash muss in main.profile implementiert werden
        return redirect(url_for("main.profile"))

    current_user.set_tidal_session(tidalapi.Session())
    login, future = current_user.get_tidal_session().login_oauth()

    current_user.set_tidal_future(future)

    thread = threading.Thread(
        target=login_thread,
        args=(
            current_app._get_current_object(),
            current_user._get_current_object(),
        ),
    )
    thread.start()

    return redirect("https://link.tidal.com/" + login.user_code)
