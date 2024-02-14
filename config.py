import os
import random

basedir = os.path.abspath(os.path.dirname(__file__))
database_path = os.path.join(basedir, "data/database.db")

class Config:
    SECRET_KEY = str(random.getrandbits(256))
    if os.environ.get("SECRET_KEY") is not None:
        SECRET_KEY = os.environ.get("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = None
    if os.environ.get("DATABASE_URI") is not None:
        if os.environ.get("DATABASE_URI").startswith("sqlite:///"):
            # Datenbank ist eine SQLite-Datenbank, bereite den Pfad vor
            os.makedirs(os.path.dirname(os.environ.get("DATABASE_URI"), exist_ok=True))
            SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URI")
        else:
            # Datenbank ist keine SQLite-Datenbank, z.B. PostgreSQL oder MySQL
            SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URI")
    else:
        os.makedirs(os.path.dirname(database_path), exist_ok=True)
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + database_path

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STATIC_FOLDER = os.path.join(basedir, "static")
