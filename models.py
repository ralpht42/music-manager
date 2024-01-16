from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, id, username, email, is_active, is_admin, tidal_session):
        self.id = id
        self.username = username
        self.email = email
        #        self.is_active = is_active # BUG: is_active muss implementiert werden
        self.is_admin = is_admin
        self.tidal_session = tidal_session
        self.future = None

    #   def __repr__(self):
    #       return f'<User {self.email}>'

    # BUG: future Objekt entfernen
    def set_future(self, future):
        self.future = future

    def get_future(self):
        return self.future

    def set_tidal_session(self, tidal_session):
        self.tidal_session = tidal_session

    def get_tidal_session(self):
        return self.tidal_session
