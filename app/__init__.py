# init.py
import os
from datetime import datetime

from flask import Flask, redirect, url_for, flash
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from config import Config

from app.extensions import db
from app.models.user import User


__version__ = "0.4.1"


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate = Migrate(app, db) # Datenbankmigrationen

    """
    Einzelne Teile der App werden in Blueprints organisiert.
    Die Blueprints werden in den jeweiligen Dateien definiert.
    Hier werden sie importiert und registriert, damit sie verwendet werden können.
    """
    from app.jobs import bp as jobs_blueprint

    app.register_blueprint(jobs_blueprint)

    from app.auth import bp as auth_blueprint

    app.register_blueprint(auth_blueprint)

    from app.main import bp as main_blueprint

    app.register_blueprint(main_blueprint)

    from app.playlists import bp as playlists_blueprint

    app.register_blueprint(playlists_blueprint)

    from app.songs import bp as songs_blueprint

    app.register_blueprint(songs_blueprint)

    """
    Die Login-Verwaltung wird über Flask-Login realisiert.
    Die Login-Methode wird über die Funktion load_user() so angepasst,
    dass die Benutzerinformationen über den Primärschlüssel der Benutzer geladen werden.
    """
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        user = User.query.get(int(user_id))
        try:
            user.load_tidal_session()
        except Exception as e:
            print(
                f"Fehler beim Laden der TIDAL-Session für den Benutzer {user.username}:\n{e}"
            )
            flash(f"Fehler beim Laden der TIDAL-Session", "danger")
        return user

    @login_manager.unauthorized_handler
    def unauthorized():
        # Wenn der Benutzer nicht eingeloggt ist, wird er auf die Login-Seite weitergeleitet
        return redirect(url_for("auth.login"))

    # Filter für die Darstellung von Datumsangaben, der in den Templates verwendet werden kann
    # Beispiel: {{ job.created_at | date_format }}
    # Das Datum wird dann im Format "dd.mm.yyyy" statt "yyyy-mm-dd hh:mm:ss.ms" angezeigt
    @app.template_filter('date_format')
    def date_format(value):
        return value.strftime("%d.%m.%Y")

    # Erstelle die Tabellen in der Datenbank, falls sie noch nicht existieren
    # Es wird noch keine Migration durchgeführt, falls sich das Datenbankschema ändert,
    # daher müssen die Tabellen manuell gelöscht werden, damit sie neu erstellt werden können
    # TODO: Datenbankmigrationen implementieren
    with app.app_context():
        db.create_all()

    return app


app = create_app()  # Wird auch von Gunicorn verwendet, um die App zu starten

if __name__ == "__main__":
    app.run()
