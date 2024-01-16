# init.py
import os

from flask import Flask, redirect, url_for
from flask_login import LoginManager

from database import init_database, get_user_by_id

__version__ = "0.2.0"


def create_app():
    app = Flask(__name__)

    if os.environ.get("SECRET_KEY") is None:
        print(
            "Es wurde keine Umgebungsvariable SECRET_KEY gefunden. Es wird eine zufällige Zeichenkette verwendet."
        )
        print(
            "Bitte setzen Sie die Umgebungsvariable SECRET_KEY, um die Sicherheit der Anwendung zu erhöhen."
        )
        print(
            "Wenn ein zufälliger Schlüssel verwendet wird, müssen alle Benutzer sich nach jedem Neustart der Anwendung erneut anmelden."
        )
        import random, string

        app.config["SECRET_KEY"] = "".join(
            random.choice(string.ascii_letters) for i in range(32)
        )
    else:
        app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

    """
    # Aufgrund von Limitierungen der TIDAL-API sind die folgenden Umgebungsvariablen 
    # nicht mehr erforderlich. Sobald die Anwendung weit genug entwickelt ist, 
    # wird möglicherweise die Entwicklung mit der TIDAL-API fortgesetzt.
    if (
        os.environ.get("TIDAL_APP_CLIENT_ID") is None
        or os.environ.get("TIDAL_APP_CLIENT_SECRET") is None
    ):
        raise Exception(
            "TIDAL_APP_CLIENT_ID oder TIDAL_APP_CLIENT_SECRET nicht gesetzt."
        )
    else:
        app.config["TIDAL_APP_CLIENT_ID"] = os.environ.get("TIDAL_APP_CLIENT_ID")
        app.config["TIDAL_APP_CLIENT_SECRET"] = os.environ.get(
            "TIDAL_APP_CLIENT_SECRET"
        )
        app.config["TIDAL_APP_TOKEN"] = None # Wird bei den Aufrufen der TIDAL-API gesetzt, falls noch nicht gesetzt
    """
    init_database()

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        # Benutzerinformationen werden über den Primärschlüssel geladen
        return get_user_by_id(user_id)

    @login_manager.unauthorized_handler
    def unauthorized():
        # Wenn der Benutzer nicht eingeloggt ist, wird er auf die Login-Seite weitergeleitet
        return redirect(url_for("auth.login"))

    # blueprint for auth routes in our app
    from auth import auth as auth_blueprint

    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    from main import main as main_blueprint

    app.register_blueprint(main_blueprint)

    # blueprint for music management parts of app
    from music import music as music_blueprint

    app.register_blueprint(music_blueprint)

    return app


app = create_app()  # Wird auch von Gunicorn verwendet, um die App zu starten

if __name__ == "__main__":
    app.run()
