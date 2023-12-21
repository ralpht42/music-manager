# database.py
import sqlite3
import re
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from argon2.low_level import Type
from faker import Faker

from models import User

# Empfehlung: https://www.owasp.org/index.php/Password_Storage_Cheat_Sheet#argon2id
# Stand 2023-12-21
# Ausgeglichen zwischen CPU- und Speicherkosten
ph = PasswordHasher(time_cost=3, memory_cost=12288, parallelism=1, type=Type.ID)

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
        username TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT 1,
        is_admin BOOLEAN NOT NULL DEFAULT 0
    )"""
    )

    # TODO: Weitere Tabellen anlegen
    conn.commit()
    conn.close()


def signup_user(username, email, password_input):
    """
    Speichert einen neuen Benutzer in der Datenbank

    :param username: Benutzername des Benutzers
    :param email: E-Mail-Adresse des Benutzers
    :param password_input: Passwort des Benutzers
    :return: None
    """
    if len(username) > 255:
        raise Exception("Benutzername darf maximal 255 Zeichen lang sein!")
    if len(email) > 255:
        raise Exception("E-Mail-Adresse darf maximal 255 Zeichen lang sein!")
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise Exception("E-Mail-Adresse ist ungültig!")
    if email == "" or email == None:
        raise Exception("E-Mail-Adresse darf nicht leer sein!")
    if password_input == "" or password_input == None:
        raise Exception("Passwort darf nicht leer sein!")

    conn, c = open_database()

    # Überprüfe, ob die E-Mail-Adresse bereits verwendet wird
    c.execute("SELECT email FROM users WHERE email = ?", (email,))
    result = c.fetchone()
    if result is not None:
        conn.close()
        raise Exception("E-Mail-Adresse wird bereits verwendet!")
    else:
        password_argon2 = ph.hash(password_input)

        # Speichere den Benutzer in der Datenbank
        c.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, password_argon2),
        )
        conn.commit()
        c.execute(
            "SELECT id, username, email, is_admin FROM users WHERE email = ?", (email,)
        )
        result = c.fetchone()
        user = User(result[0], result[1], result[2], bool(result[3]))
        conn.close()
        return user


def login_user(email, password_input):
    """
    Überprüft die E-Mail-Adresse und das Passwort des Benutzers

    :param email: E-Mail-Adresse des Benutzers
    :param password: Gehashtes Passwort des Benutzers (SHA-384, salt + password + pepper)
    :return: True, wenn die E-Mail-Adresse und das Passwort korrekt sind, sonst False
    :rtype: bool
    """
    conn, c = open_database()

    # TODO: Fehlgeschlagene Anmeldeversuche in Log-Datei schreiben, um Brute-Force-Angriffe zu erkennen
    # Überprüfe, ob die E-Mail-Adresse und das Passwort den Anforderungen entsprechen
    if (
        email == ""
        or password_input == ""
        or email == None
        or password_input == None
        or len(email) > 255
        or len(email) == 0
        or len(password_input) < 8
        or not re.match(r"[^@]+@[^@]+\.[^@]+", email)
    ):
        conn.close()
        raise Exception("E-Mail-Adresse oder Passwort ist falsch!")

    # Überprüfe, ob die E-Mail-Adresse nicht registriert ist
    c.execute("SELECT email FROM users WHERE email = ?", (email,))
    result = c.fetchone()
    if result is None:
        conn.close()
        # TODO: Fehlgeschlagene Anmeldeversuche in Log-Datei schreiben, um Brute-Force-Angriffe zu erkennen
        raise Exception("E-Mail-Adresse oder Passwort ist falsch!")

    c.execute("SELECT password FROM users WHERE email = ?", (email,))
    password_db = c.fetchone()[0]
    try:
        if ph.verify(password_db, password_input):
            c.execute(
                "SELECT id, username, email, is_admin FROM users WHERE email = ?",
                (email,),
            )
            result = c.fetchone()
            user = User(result[0], result[1], result[2], bool(result[3]))

            if ph.check_needs_rehash(password_db):
                print("Passwort für " + email + " wird neu gehasht")
                new_hash = ph.hash(password_input)
                c.execute(
                    "UPDATE users SET password = ? WHERE email = ?",
                    (new_hash, email),
                )
                conn.commit()

            conn.close()
            return user
    except VerifyMismatchError:
        conn.close()
        raise Exception("E-Mail-Adresse oder Passwort ist falsch!")
    except Exception as e:
        conn.close()
        raise Exception(e)  # Gebe den Fehler weiter an die aufrufende Funktion


def get_user_by_id(user_id):
    """
    Gibt einen Benutzer anhand seiner ID zurück

    :param user_id: ID des Benutzers
    :return: Benutzer
    :rtype: User
    """
    conn, c = open_database()
    c.execute(
        "SELECT id, username, email, is_admin FROM users WHERE id = ?", (user_id,)
    )
    result = c.fetchone()
    if result is None:
        conn.close()
        # TODO: Überprüfen
        # raise Exception("Benutzer mit ID " + str(user_id) + " nicht gefunden")
        return None
    user = User(result[0], result[1], result[2], bool(result[3]))
    conn.close()
    return user


if __name__ == "__main__":
    debug_mode = True  # Demo-Datenbank verwenden

    ph = PasswordHasher()

    init_database()

    # Erstelle Demo-Daten
    fake = Faker()
    fake_username = fake.user_name()
    print("Erstelle Demo-Daten für Benutzername " + fake_username)
    fake_email = fake.email()
    print("Erstelle Demo-Daten für E-Mail-Adresse " + fake_email)
    fake_password_input = fake.password(
        length=8, special_chars=False, digits=True, upper_case=True, lower_case=True
    )
    print("Das Passwort ist " + fake_password_input)

    # Teste den Registrierungsprozess
    try:
        user = signup_user(fake_username, fake_email, fake_password_input)
        print("Registrierung erfolgreich")
    except Exception as e:
        print("Fehler: " + str(e))

    # Teste den Login-Prozess
    try:
        user = login_user(fake_email, fake_password_input)
        print("Login erfolgreich")
    except Exception as e:
        print("Fehler: " + str(e))
