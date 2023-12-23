# init.py
import os

from flask import Flask, redirect, url_for
from flask_login import LoginManager

from database import init_database, get_user_by_id


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY')

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


app = create_app() # Wird auch von Gunicorn verwendet, um die App zu starten

# Für das lokale Testen der App (ohne Gunicorn, z.B. mit "python app.py")
# Es wird empfohlen, eine virtuelle Umgebung zu verwenden (z.B. mit "python -m venv venv")
# und die Abhängigkeiten mit "pip install -r requirements.txt" zu installieren
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
