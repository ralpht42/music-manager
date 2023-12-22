from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, username:str, email: str, is_admin: bool): # BUG: is_active muss implementiert werden
        self.id = id
        self.username = username
        self.email = email
        self.is_admin = is_admin

        self.tidal_account = 

 #   def __repr__(self):
 #       return f'<User {self.email}>'