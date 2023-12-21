# init.py

from flask import Flask, redirect, url_for
from flask_login import LoginManager

from database import init_database, get_user_by_id

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'CvyZWUaNANYc8SbwsMTxAwoNMyRVM2'

    init_database()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
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

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host="0.0.0.0", port=3000, debug=True)