# database.py
import sqlite3
import re
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from argon2.low_level import Type
from faker import Faker
from datetime import time, datetime
import pandas as pd
import math
import tidalapi

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
        conn = sqlite3.connect("./data/demo-database.db")
    else:
        # print("Datenbank wird geöffnet.")
        conn = sqlite3.connect("./data/database.db")
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON")  # Aktiviere die Fremdschlüsselunterstützung

    return conn, c


def init_database():
    """
    Initialisiert die Datenbank und legt die Tabellen an

    :return: None
    """
    # Benutzer Tabelle
    conn, c = open_database()
    c.execute(
        """CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT 1,
        is_admin BOOLEAN NOT NULL DEFAULT 0,
        tidal_account_id INTEGER,

        FOREIGN KEY(tidal_account_id) REFERENCES tidal_credentials(id)
    )"""
    )

    # TIDAL Account Tabelle
    c.execute(
        """CREATE TABLE IF NOT EXISTS tidal_credentials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token_type TEXT NOT NULL,
        access_token TEXT NOT NULL,
        refresh_token TEXT NOT NULL,
        expiry_time INTEGER NOT NULL
    )"""
    )

    # Über Excel Tabelle importierte Songs
    # Besonderheiten: Es gibt nicht für jeden Song alle Informationen, daher sind einige Felder NULL
    c.execute(
        """CREATE TABLE IF NOT EXISTS excel_songs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        artists TEXT,
        year INTEGER,
        language TEXT,
        length INTEGER,
        genre TEXT,
        feels TEXT,
        type TEXT,
        gender TEXT,
        speed TEXT,
        voice_percent INTEGER,
        rap_percent INTEGER,
        popularity_percent INTEGER,
        weird_percent INTEGER,
        is_legend BOOLEAN,
        folder TEXT,
        series TEXT,
        FOREIGN KEY(job_id) REFERENCES jobs(id)
    )"""
    )

    # Job Tabelle
    c.execute(
        """CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        created_by INTEGER NOT NULL,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        updated_by INTEGER NOT NULL,
        manual BOOLEAN NOT NULL,

        FOREIGN KEY(created_by) REFERENCES users(id),
        FOREIGN KEY(updated_by) REFERENCES users(id)
    )"""
    )

    # Playlist Tabelle
    # TODO: Playlist Cover erstellen, bearbeiten und löschen
    c.execute(
        """CREATE TABLE IF NOT EXISTS playlists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        created_by INTEGER NOT NULL,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        updated_by INTEGER NOT NULL,

        FOREIGN KEY(created_by) REFERENCES users(id),
        FOREIGN KEY(updated_by) REFERENCES users(id)
    )"""
    )

    # Playlist-Song Zuordnung
    c.execute(
        """CREATE TABLE IF NOT EXISTS playlist_song (
        playlist_id INTEGER NOT NULL,
        song_id INTEGER NOT NULL

        FOREIGN KEY(playlist_id) REFERENCES playlists(id),
        FOREIGN KEY(song_id) REFERENCES songs(id)
    )"""
    )

    # Song Tabelle
    c.execute(
        """CREATE TABLE IF NOT EXISTS songs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        release_date TEXT,
        duration INTEGER,
        explicit BOOLEAN,
        
        isrc TEXT,
        popularity INTEGER,
        tidal_id INTEGER,
        tidal_cover INTEGER,
    )"""
    )

    # Artist Tabelle
    c.execute(
        """CREATE TABLE IF NOT EXISTS artists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        real_name TEXT,
        tidal_id INTEGER,
        tidal_cover INTEGER,
    )"""
    )

    # Rolle Tabelle
    c.execute(
        """CREATE TABLE IF NOT EXISTS artist_roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
    )"""
    )

    # Song-Artist-Rolle Zuordnung
    c.execute(
        """CREATE TABLE IF NOT EXISTS song_artist (
        song_id INTEGER NOT NULL,
        artist_id INTEGER NOT NULL,
        role_id INTEGER NOT NULL,

        FOREIGN KEY(song_id) REFERENCES songs(id),
        FOREIGN KEY(artist_id) REFERENCES artists(id)
        FOREIGN KEY(role_id) REFERENCES artist_roles(id)
    )"""
    )

    # Gesungene Sprache Tabelle
    # Die Sprache wird als ISO 639-1 Code gespeichert, z. B. "de" für Deutsch oder "en" für Englisch
    c.execute(
        """CREATE TABLE IF NOT EXISTS languages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
    )"""
    )

    # Gesungene Sprache zu Song Zuordnung
    c.execute(
        """CREATE TABLE IF NOT EXISTS language_song (
        language_id INTEGER NOT NULL,
        song_id INTEGER NOT NULL,

        FOREIGN KEY(language_id) REFERENCES languages(id),
        FOREIGN KEY(song_id) REFERENCES songs(id)
    )"""
    )

    # Genre Tabelle
    c.execute(
        """CREATE TABLE IF NOT EXISTS genres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )"""
    )

    # Genre-Song Zuordnung
    c.execute(
        """CREATE TABLE IF NOT EXISTS genre_song (
        genre_id INTEGER NOT NULL,
        song_id INTEGER NOT NULL,

        FOREIGN KEY(genre_id) REFERENCES genres(id),
        FOREIGN KEY(song_id) REFERENCES songs(id)
    )"""
    )

    # Stimmung Tabelle
    c.execute(
        """CREATE TABLE IF NOT EXISTS feels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
    )"""
    )

    # Stimmung-Song Zuordnung
    c.execute(
        """CREATE TABLE IF NOT EXISTS feel_song (
        feel_id INTEGER NOT NULL,
        song_id INTEGER NOT NULL,

        FOREIGN KEY(feel_id) REFERENCES feels(id),
        FOREIGN KEY(song_id) REFERENCES songs(id)
    )"""
    )

    # Typ Tabelle
    # Ein Song kann nur einen Typ haben, z. B. "Original", "Cover", "Remix" usw.
    c.execute(
        """CREATE TABLE IF NOT EXISTS types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
    )"""
    )

    # Geschwindigkeit Tabelle
    c.execute(
        """CREATE TABLE IF NOT EXISTS speeds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
    )"""
    )

    # Geschwindigkeit-Song Zuordnung
    c.execute(
        """CREATE TABLE IF NOT EXISTS speed_song (
        speed_id INTEGER NOT NULL,
        song_id INTEGER NOT NULL,

        FOREIGN KEY(speed_id) REFERENCES speeds(id),
        FOREIGN KEY(song_id) REFERENCES songs(id)
    )"""
    )

    # Ordner Tabelle
    c.execute(
        """CREATE TABLE IF NOT EXISTS folders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
    )"""
    )

    # Ordner-Song Zuordnung
    c.execute(
        """CREATE TABLE IF NOT EXISTS folder_song (
        folder_id INTEGER NOT NULL,
        song_id INTEGER NOT NULL,

        FOREIGN KEY(folder_id) REFERENCES folders(id),
        FOREIGN KEY(song_id) REFERENCES songs(id)
    )"""
    )

    # Serie Tabelle
    c.execute(
        """CREATE TABLE IF NOT EXISTS series (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
    )"""
    )

    # Serie-Song Zuordnung
    c.execute(
        """CREATE TABLE IF NOT EXISTS series_song (
        series_id INTEGER NOT NULL,
        song_id INTEGER NOT NULL,

        FOREIGN KEY(series_id) REFERENCES series(id),
        FOREIGN KEY(song_id) REFERENCES songs(id)
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
        user_id = c.lastrowid
        conn.commit()
        conn.close()

        # Lade den Benutzer aus der Datenbank und gebe ihn zurück
        return get_user_by_id(user_id)


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
                "SELECT id FROM users WHERE email = ?",
                (email,),
            )
            user_id = c.fetchone()[0]

            # Überprüfe, ob das Passwort neu gehasht werden muss
            if ph.check_needs_rehash(password_db):
                print("Passwort für " + email + " wird neu gehasht")
                new_hash = ph.hash(password_input)
                c.execute(
                    "UPDATE users SET password = ? WHERE email = ?",
                    (new_hash, email),
                )
                conn.commit()

            conn.close()
            return get_user_by_id(user_id)
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
        "SELECT id, username, email, is_active, is_admin, tidal_account_id FROM users WHERE id = ?",
        (user_id,),
    )
    user_result = c.fetchone()
    if user_result is None:
        conn.close()
        # TODO: Überprüfen
        # raise Exception("Benutzer mit ID " + str(user_id) + " nicht gefunden")
        return None

    # Tidal Account laden, falls vorhanden
    c.execute(
        "SELECT id, token_type, access_token, refresh_token, expiry_time FROM tidal_credentials WHERE id = ?",
        (user_result[5],),
    )
    tidal_account_result = c.fetchone()

    # Tidal Session Objekt erstellen
    tidal_session = None
    if tidal_account_result is not None:
        if tidal_account_result[4] < datetime.now().timestamp():
            # Token ist abgelaufen, hole neuen Token
            raise Exception("TIDAL-Token ist abgelaufen, erneuter Login erforderlich!")
        else:
            # Token ist noch gültig
            tidal_session = tidalapi.Session()
            tidal_session.load_oauth_session(
                tidal_account_result[1],
                tidal_account_result[2],
                tidal_account_result[3],
                tidal_account_result[4],
            )

    user = User(
        user_result[0],
        user_result[1],
        user_result[2],
        bool(user_result[3]),
        bool(user_result[4]),
        tidal_session,
    )
    conn.close()
    return user


def import_excel_songs_manually(excel_file, user_id):
    """
    Importiert die Songs aus einer Excel-Datei eine temporäre Tabelle.
    Die Einträge stehen im Anschluss für eine weitere Verarbeitung zur Verfügung. (automatisch oder manuell)

    :param excel_file: Excel-Datei
    :return: None
    """
    conn, c = open_database()

    # Erstelle einen neuen Job
    name = "Manueller Excel-Import " + datetime.now().strftime(
        "am %d.%m.%Y um %H:%M:%S Uhr"
    )
    c.execute(
        "INSERT INTO jobs (name, created_by, updated_by, manual) VALUES (?, ?, ?, ?)",
        (name, user_id, user_id, True),
    )
    job_id = c.lastrowid

    try:
        df = pd.read_excel(excel_file)
    except Exception as e:
        raise Exception("Excel-Datei konnte nicht gelesen werden: " + str(e))

    for index, row in df.iterrows():
        # Gehe jede Zeile durch und übertrage die Daten in die Datenbank
        # Trenne den Titel und den Interpreten
        title_parts = row["Title"].split(" - ")
        if len(title_parts) > 1:
            artists = title_parts[0].strip()
            title = title_parts[1].strip()
        else:
            title = title_parts[0].strip()
            artists = None
        if math.isnan(row["Year"]):
            year = None
        else:
            year = int(row["Year"])
        language = row["Language"]
        if type(row["Length"]) == time:
            length_in_seconds = (
                row["Length"].hour * 3600
                + row["Length"].minute * 60
                + row["Length"].second
            )
        else:
            length_in_seconds = None
        genre = row["Genre"]
        feels = row["Feels"]
        type_ = row["Type"]
        speed = row["Speed"]
        if math.isnan(row["Voice %"]):
            voice_percent = None
        else:
            voice_percent = int(row["Voice %"]) / 100

        if math.isnan(row["Rap % from Voice"]):
            rap_percent = None
        else:
            rap_percent = int(row["Rap % from Voice"]) / 100

        if math.isnan(row["Popularity %"]):
            popularity_percent = None
        else:
            popularity_percent = int(row["Popularity %"]) / 100

        if math.isnan(row["Weird %"]):
            weird_percent = None
        else:
            weird_percent = int(row["Weird %"]) / 100
        is_legend = True if row["Legend"] == 1 else False
        folder = row["Folder"]
        series = row["Series"]

        # Speichere jeden Song in der Datenbank
        c.execute(
            """INSERT INTO excel_songs (
            job_id, title, artists, year, language, length, genre, feels, 
            type, speed, voice_percent, rap_percent, popularity_percent, 
            weird_percent, is_legend, folder, series
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                job_id,
                title,
                artists,
                year,
                language,
                length_in_seconds,
                genre,
                feels,
                type_,
                speed,
                voice_percent,
                rap_percent,
                popularity_percent,
                weird_percent,
                is_legend,
                folder,
                series,
            ),
        )

    conn.commit()
    conn.close()
    # Gehe jede Zeile durch und übertrage die Daten in die Datenbank


def get_jobs_by_user_id(user_id):
    """
    Gibt eine Liste mit Jobs zurück, die zu einem Benutzer gehören

    :param user_id: ID des Benutzers
    :return: Liste mit Jobs
    :rtype: list
    """
    conn, c = open_database()

    c.execute(
        "SELECT jobs.id, jobs.name, jobs.created_at, created_by.username, jobs.updated_at, updated_by.username, jobs.manual FROM jobs JOIN users AS created_by ON jobs.created_by = created_by.id JOIN users AS updated_by ON jobs.updated_by = updated_by.id WHERE created_by.id = ?",
        (user_id,),
    )
    result = c.fetchall()
    if result is None:
        conn.close()
        return None
    jobs = []
    for row in result:
        jobs.append(
            {
                "id": row[0],
                "name": row[1],
                "created_at": row[2],
                "created_by": row[3],
                "updated_at": row[4],
                "updated_by": row[5],
                "manual": row[6],
            }
        )

    conn.close()
    return jobs


def get_job_by_id(job_id):
    """
    Gibt alle Songs eines Jobs zurück

    :param job_id: ID des Jobs
    :return: Job
    :rtype: dict
    """
    conn, c = open_database()

    # Entscheide, ob der Job manuell oder automatisch erstellt wurde
    c.execute("SELECT manual FROM jobs WHERE id = ?", (job_id,))
    result = c.fetchone()
    if result is None:
        conn.close()
        raise Exception("Job mit ID " + str(job_id) + " nicht gefunden")
    manual = bool(result[0])

    if manual:
        # Lade die Songs aus der Tabelle excel_songs
        c.execute(
            """SELECT id, title, artists, year, language, length, genre,
            feels, type, speed, voice_percent, rap_percent, popularity_percent,
            weird_percent, is_legend, folder, series FROM excel_songs 
            WHERE job_id = ?""",
            (job_id,),
        )
        result = c.fetchall()
        if result is None:
            conn.close()
            return None
        songs = []
        for row in result:
            songs.append(
                {
                    "id": row[0],
                    "title": row[1],
                    "artists": row[2],
                    "year": row[3],
                    "language": row[4],
                    "length": row[5],
                    "genre": row[6],
                    "feels": row[7],
                    "type": row[8],
                    "speed": row[9],
                    "voice_percent": row[10],
                    "rap_percent": row[11],
                    "popularity_percent": row[12],
                    "weird_percent": row[13],
                    "is_legend": row[14],
                    "folder": row[15],
                    "series": row[16],
                }
            )

        # Lade die Informationen zum Job
        c.execute(
            """SELECT jobs.id, jobs.name, jobs.created_at, created_by.username, 
            jobs.updated_at, updated_by.username, manual FROM jobs 
            JOIN users AS created_by ON jobs.created_by = created_by.id 
            JOIN users AS updated_by ON jobs.updated_by = updated_by.id 
            WHERE jobs.id = ?""",
            (job_id,),
        )
        result = c.fetchone()
        if result is None:
            conn.close()
            return None
        job = {
            "id": result[0],
            "name": result[1],
            "created_at": result[2],
            "created_by": result[3],
            "updated_at": result[4],
            "updated_by": result[5],
            "manual": result[6],
            "songs": songs,
        }

        conn.close()
        return job
    else:
        # TODO: Inhalte von automatischen Jobs laden
        pass


def delete_job_by_id(job_id):
    """
    Löscht einen Job anhand seiner ID

    :param job_id: ID des Jobs
    :return: None
    """
    conn, c = open_database()

    # Entscheide, ob der Job manuell oder automatisch erstellt wurde
    c.execute("SELECT manual FROM jobs WHERE id = ?", (job_id,))
    result = c.fetchone()
    if result is None:
        conn.close()
        raise Exception("Job mit ID " + str(job_id) + " nicht gefunden")
    manual = bool(result[0])

    # Lösche die Songs, die zu dem Job gehören
    if manual:
        # Lösche die Songs aus der Tabelle excel_songs
        c.execute("DELETE FROM excel_songs WHERE job_id = ?", (job_id,))
    else:
        # TODO: Inhalte von automatischen Jobs löschen
        pass

    # Lösche den Job
    c.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()


def edit_job_by_id(job_id, settings):
    """
    Bearbeitet einen Job anhand seiner ID

    :param job_id: ID des Jobs
    :param settings: Einstellungen für den Job
    :return: None
    """
    # TODO: Implementieren
    pass


def create_playlist_from_job(job_id):
    """
    Überträgt die Songs eines Jobs in eine neue Playlist.
    Dabei werden die Songs in TIDAL gesucht und die entsprechenden IDs gespeichert.
    Zugehörige Songs werden ebenfalls gesucht und die IDs gespeichert.
    Anschließend wird die Playlist erstellt und die Songs hinzugefügt.

    :param job_id: ID des Jobs
    :return: playlist_id
    :rtype: int
    """


def get_playlist_by_id(playlist_id):
    """
    Gibt eine Playlist anhand ihrer ID zurück

    :param playlist_id: ID der Playlist
    :return: Playlist
    :rtype: dict
    """
    pass


def add_tidal_token(user_id, tidal_token):
    """
    Fügt einen TIDAL-Token zu einem Benutzer hinzu

    :param user_id: ID des Benutzers
    :param tidal_token: TIDAL-Token (access_token, refresh_token, expiry_time, token_type)
    :return: None
    """
    conn, c = open_database()

    # Speichere den TIDAL-Account in der Datenbank
    c.execute(
        "INSERT INTO tidal_credentials (token_type, access_token, refresh_token, expiry_time) VALUES (?, ?, ?, ?)",
        (
            tidal_token["token_type"],
            tidal_token["access_token"],
            tidal_token["refresh_token"],
            tidal_token["expiry_time"].timestamp(),
        ),
    )
    tidal_account_id = c.lastrowid

    # Verknüpfe den TIDAL-Account mit dem Benutzer
    c.execute(
        "UPDATE users SET tidal_account_id = ? WHERE id = ?",
        (tidal_account_id, user_id),
    )
    conn.commit()
    conn.close()


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
