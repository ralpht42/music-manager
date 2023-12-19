import sqlite3
import hashlib
import uuid
import re

from faker import Faker

pepper = "cpDZcVuhWZcmfDh2oQ2EzRm82Qjvf3"  # TODO: Geheimen Schlüssel aus Umgebungsvariablen laden

debug_mode = False  # True, wenn die Demo-Datenbank verwendet werden soll


def open_database():
    """
    Öffnet die Datenbank und gibt die Verbindung und den Cursor zurück

    :return: Verbindung und Cursor
    :rtype: tuple
    """
    if debug_mode:
        # print("Demo Datenbank wird geöffnet.")
        conn = sqlite3.connect("demo-database.db")
    else:
        # print("Datenbank wird geöffnet.")
        conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON")  # Aktiviere die Fremdschlüsselunterstützung

    return conn, c


def init_database():
    """
    Initialisiert die Datenbank und legt die Tabellen an

    :return: None
    """
    conn, c = open_database()
    c.execute(
        """CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        salt TEXT NOT NULL
    )"""
    )

    # TODO: Weitere Tabellen anlegen
    conn.commit()
    conn.close()


def signup_user(email, password):
    """
    Speichert einen neuen Benutzer in der Datenbank

    :param email: E-Mail-Adresse des Benutzers
    :param password: Gehashtes Passwort des Benutzers (SHA-384)
    :return: None
    """
    if len(password) != 96:
        raise Exception("Das Passwort muss ein SHA-384 Hash sein")        
    if len(email) > 255:
        raise Exception("E-Mail-Adresse darf maximal 255 Zeichen lang sein")
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise Exception("E-Mail-Adresse ist ungültig")
    if email == "":
        raise Exception("E-Mail-Adresse darf nicht leer sein")
    if password == "":
        raise Exception("Passwort darf nicht leer sein")

    conn, c = open_database()

    # Überprüfe, ob die E-Mail-Adresse bereits verwendet wird
    c.execute("SELECT email FROM users WHERE email = ?", (email,))
    result = c.fetchone()
    if result is not None:
        conn.close()
        raise Exception("E-Mail-Adresse wird bereits verwendet")
    else:
        salt = uuid.uuid4().hex
        password = hashlib.sha384((salt + password + pepper).encode()).hexdigest()
        c.execute(
            "INSERT INTO users (email, password, salt) VALUES (?, ?, ?)",
            (email, password, salt),
        )
        print("Benutzer mit E-Mail-Adresse " + email + " wurde angelegt.")
        conn.commit()
        conn.close()


def login_user(email, password_input):
    """
    Überprüft die E-Mail-Adresse und das Passwort des Benutzers

    :param email: E-Mail-Adresse des Benutzers
    :param password: Gehashtes Passwort des Benutzers (SHA-384, salt + password + pepper)
    :return: True, wenn die E-Mail-Adresse und das Passwort korrekt sind, sonst False
    :rtype: bool
    """
    conn, c = open_database()

    c.execute("SELECT email FROM users WHERE email = ?", (email,))
    result = c.fetchone()
    if result is None:
        conn.close()
        return False  # E-Mail-Adresse existiert nicht, aus Sicherheitsgründen wird False zurückgegeben

    c.execute("SELECT salt, password FROM users WHERE email = ?", (email,))
    result = c.fetchone()
    salt = result[0]
    password_db = result[1]
    password_input_hashed = hashlib.sha384(
        (salt + password_input + pepper).encode()
    ).hexdigest()

    if password_input_hashed == password_db:
        conn.close()
        return True  # Passwort ist korrekt
    else:
        conn.close()
        return False  # Passwort ist falsch


if __name__ == "__main__":
    debug_mode = True  # Demo-Datenbank verwenden

    conn, c = open_database()

    # Erstelle Demo-Daten
    fake = Faker()
    fake_email = fake.email()
    print("Erstelle Demo-Daten für E-Mail-Adresse " + fake_email)
    fake_password_input_hashed = hashlib.sha384(fake.password().encode()).hexdigest()
    print("Das gehashte Passwort ist " + fake_password_input_hashed)

    # Teste den Registrierungsprozess
    signup_user(fake_email, fake_password_input_hashed)

    # Teste den Login-Prozess
    print(
        "Der Anmeldeprozess war "
        + (
            "erfolgreich"
            if login_user(fake_email, fake_password_input_hashed)
            else "nicht erfolgreich"
        )
    )

    conn.close()
