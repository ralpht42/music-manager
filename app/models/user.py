from datetime import datetime
import requests
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from argon2.low_level import Type
import tidalapi

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(60), index=True, unique=True, nullable=False)
    email = db.Column(db.String(60), index=True, unique=True, nullable=False)
    # Überprüfen, welche Zeichenlänge hier sinnvoll ist (argon2id)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_authenticated = db.Column(db.Boolean, default=False, nullable=False)
    tidal_account_id = db.Column(db.Integer, db.ForeignKey("tidal_accounts.id"))
    tidal_account = db.relationship("TidalAccount", backref="user", uselist=False)

    tidal_session = None
    tidal_future = None

    # Empfehlung: https://www.owasp.org/index.php/Password_Storage_Cheat_Sheet#argon2id
    # Stand 2023-12-21
    # Ausgeglichen zwischen CPU- und Speicherkosten
    __ph = PasswordHasher(time_cost=3, memory_cost=12288, parallelism=1, type=Type.ID)

    def __init__(self, username, email, password, is_admin=False):
        self.username = username
        self.email = email
        self.set_password(password)
        self.is_admin = is_admin

    def __repr__(self):
        return f"<User {self.email}>"

    def get_id(self):
        return self.id

    def is_active(self):
        return self.is_active

    def is_authenticated(self):
        return self.is_authenticated

    def is_anonymous(self):
        return False

    # Könnte zu Problemen führen, falls der Commit eine laufende Transaktion beendet.
    # TODO: Evaluiere, ob das ein Problem ist und ob es eine bessere Lösung gibt.
    def check_password(self, password):
        try:
            self.__ph.verify(self.password_hash, password)

            # Wenn das Passwort korrekt ist, wird überprüft, ob es neu gehasht werden muss
            if self.__ph.check_needs_rehash(self.password_hash):
                self.set_password(password)
                db.session.commit()
            return True
        except VerifyMismatchError:
            return False

    def set_password(self, password):
        hash = self.__ph.hash(password)
        self.password_hash = hash

    # future und tidal_session sind nicht in der Datenbank, sondern Objekte,
    # die in der Session gespeichert werden und beim Login erstellt werden

    def set_tidal_future(self, future):
        self.tidal_future = future

    def get_tidal_future(self):
        return self.tidal_future

    def set_tidal_session(self, tidal_session):
        self.tidal_session = tidal_session

    def get_tidal_session(self):
        return self.tidal_session

    def load_tidal_session(self):
        if self.tidal_account is not None:
            self.tidal_session = tidalapi.Session()
            # Überprüfen, ob die Anmeldung bei TIDAL noch gültig ist
            if self.tidal_account.expiry_time < datetime.now():
                try:
                    self.tidal_session.token_refresh(self.tidal_account.refresh_token)
                except requests.exceptions.ConnectionError as e:
                    print(
                        f"Der TIDAL-Token für den Benutzer {self.username} konnte nicht aktualisiert werden.\nVermutlich besteht keine Verbindung zu den TIDAL-Servern:\n{e}"
                    )
                    raise Exception(
                        f"Der TIDAL-Token für den Benutzer {self.username} konnte nicht aktualisiert werden.\nVermutlich besteht keine Verbindung zu den TIDAL-Servern:\n{e}"
                    )

                # Aktualisiere die Daten in der Datenbank
                self.tidal_account.access_token = self.tidal_session.access_token
                # Aktualisiere nicht den Refresh-Token, da dieser None ist (eventuell ein Bug in tidalapi)
                # self.tidal_account.refresh_token = self.tidal_session.refresh_token # BUG:
                self.tidal_account.expiry_time = self.tidal_session.expiry_time
                db.session.add(self.tidal_account)
                db.session.commit()

            # Fehlerbehandelung, falls keine Verbindung zu den TIDAL Servern hergestellt werden kann.
            # Das ist der Fall, falls der Server keine Internetverbindung hat oder die TIDAL Server nicht verfügbar sind.
            try:
                self.tidal_session.load_oauth_session(
                    "Bearer",
                    self.tidal_account.access_token,
                    self.tidal_account.refresh_token,
                    self.tidal_account.expiry_time,
                )
            except requests.exceptions.ConnectionError as e:
                print(
                    f"Es konnte keine Verbindung zu den Tidal-Servern hergestellt werden: {e}"
                )
                raise Exception(
                    f"Der TIDAL-Token für den Benutzer {self.username} konnte nicht aktualisiert werden.\nVermutlich besteht keine Verbindung zu den TIDAL-Servern:\n{e}"
                )


class TidalAccount(db.Model):
    __tablename__ = "tidal_accounts"
    id = db.Column(db.Integer, primary_key=True)
    # token_type = "Bearer" # Es ist mit dem Login über TIDAL immer ein Bearer-Token
    access_token = db.Column(db.String(128), nullable=False)
    refresh_token = db.Column(db.String(128), nullable=False)
    expiry_time = db.Column(db.DateTime(timezone=True), nullable=False)
