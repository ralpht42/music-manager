# database.py
import sqlite3
import re
import os
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from argon2.low_level import Type
from faker import Faker
from datetime import time, datetime
import pandas as pd
import math
import tidalapi

from models import User

from flask import current_app
from flask_login import current_user

from tidaldev import search as tidal_search
from tidaldev import refresh_tidal_app_token

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
    # Erstelle den Ordner für die Datenbank, falls er noch nicht existiert
    if not os.path.exists("./data"):
        os.makedirs("./data")

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
        manual BOOLEAN NOT NULL,

        FOREIGN KEY(created_by) REFERENCES users(id),
        FOREIGN KEY(updated_by) REFERENCES users(id)
    )"""
    )

    # Playlist-Song Zuordnung
    c.execute(
        """CREATE TABLE IF NOT EXISTS playlist_song (
        playlist_id INTEGER NOT NULL,
        song_id INTEGER NOT NULL,

        FOREIGN KEY(playlist_id) REFERENCES playlists(id),
        FOREIGN KEY(song_id) REFERENCES songs(id)
    )"""
    )

    # Song Tabelle
    c.execute(
        """CREATE TABLE IF NOT EXISTS songs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        duration INTEGER,
        explicit BOOLEAN,
        type_id INTEGER,

        voice_percent INTEGER,
        rap_percent INTEGER,
        popularity_percent INTEGER,
        weird_percent INTEGER,
        
        isrc TEXT,
        popularity_tidal INTEGER,
        tidal_id INTEGER,
        album_id INTEGER,

        FOREIGN KEY(type_id) REFERENCES types(id),
        FOREIGN KEY(album_id) REFERENCES albums(id)
    )"""
    )

    # Album Tabelle
    c.execute(
        """CREATE TABLE IF NOT EXISTS albums (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        release_date TEXT,
        tidal_id INTEGER,
        tidal_cover TEXT
    )"""
    )

    # Artist Tabelle
    c.execute(
        """CREATE TABLE IF NOT EXISTS artists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        real_name TEXT,
        tidal_id INTEGER,
        tidal_cover TEXT,
        tidal_bio TEXT
    )"""
    )

    # Rolle Tabelle
    c.execute(
        """CREATE TABLE IF NOT EXISTS artist_roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )"""
    )

    # Song-Artist-Rolle Zuordnung
    c.execute(
        """CREATE TABLE IF NOT EXISTS song_artist (
        song_id INTEGER NOT NULL,
        artist_id INTEGER NOT NULL,
        role_id INTEGER NOT NULL,

        FOREIGN KEY(song_id) REFERENCES songs(id),
        FOREIGN KEY(artist_id) REFERENCES artists(id),
        FOREIGN KEY(role_id) REFERENCES artist_roles(id)
    )"""
    )

    # Gesungene Sprache Tabelle
    # Die Sprache wird als ISO 639-1 Code gespeichert, z. B. "de" für Deutsch oder "en" für Englisch
    c.execute(
        """CREATE TABLE IF NOT EXISTS languages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
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

    # Feels Tabelle
    c.execute(
        """CREATE TABLE IF NOT EXISTS feels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )"""
    )

    # Feels-Song Zuordnung
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
        name TEXT NOT NULL
    )"""
    )

    # Geschwindigkeit Tabelle
    c.execute(
        """CREATE TABLE IF NOT EXISTS speeds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
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
        name TEXT NOT NULL
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
        name TEXT NOT NULL
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

    tidal_session = None

    # Wenn ein Tidal Account vorhanden ist, dann lade die Daten in die Session
    if tidal_account_result is not None:
        # Tidal Session Objekt erstellen
        tidal_session = tidalapi.Session()

        # Überprüfe, ob der Token abgelaufen ist, wenn ja, dann hole einen neuen
        if tidal_account_result[4] < datetime.now().timestamp():
            # Token ist abgelaufen, hole neuen Token
            tidal_session.token_refresh(tidal_account_result[3])

            # Speichere den neuen Token in der Datenbank
            add_tidal_user_token(
                user_id,
                {
                    "token_type": tidal_session.token_type,
                    "access_token": tidal_session.access_token,
                    "refresh_token": tidal_account_result[
                        3
                    ],  # Der Refresh-Token ändert sich nicht, daher wird er nicht aktualisiert
                    "expiry_time": tidal_session.expiry_time,
                },
            )

            print("TIDAL-User-Token für " + user_result[2] + " wurde aktualisiert")

            # Lade den Token erneut aus der Datenbank, falls er aktualisiert wurde,
            # da durch einen Bug das Zeitformat beim aktualisieren verändert wird.
            # datetime.datetime, statt float, sowie viele Felder nicht initialisiert

            c.execute(
                """SELECT tidal_credentials.id, token_type, access_token, refresh_token, expiry_time FROM tidal_credentials 
                JOIN users AS users ON tidal_credentials.id = users.tidal_account_id
                WHERE users.id = ?
                """,
                (user_id,),
            )
            tidal_account_result = c.fetchone()

        # Token ist noch gültig
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
            """SELECT jobs.id, jobs.name, jobs.created_at, jobs.created_by, 
            created_by.username, jobs.updated_at, jobs.updated_by, 
            updated_by.username, manual FROM jobs 
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
            "created_by_username": result[4],
            "updated_at": result[5],
            "updated_by": result[6],
            "updated_by_username": result[7],
            "manual": result[8],
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


def get_job_song_by_id(job_id, song_id):
    """
    Gibt einen Song eines Jobs zurück

    :param job_id: ID des Jobs
    :param song_id: ID des Songs
    :return: Song
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
        # Lade den Song aus der Tabelle excel_songs
        c.execute(
            """SELECT id, title, artists, year, language, length, genre,
            feels, type, speed, voice_percent, rap_percent, popularity_percent,
            weird_percent, is_legend, folder, series FROM excel_songs 
            WHERE job_id = ? AND id = ?""",
            (job_id, song_id),
        )
        result = c.fetchone()
        if result is None:
            conn.close()
            raise Exception("Song mit ID " + str(song_id) + " nicht gefunden")
        song = {
            "id": result[0],
            "title": result[1],
            "artists": result[2],
            "year": result[3],
            "language": result[4],
            "length": result[5],
            "genre": result[6],
            "feels": result[7],
            "type": result[8],
            "speed": result[9],
            "voice_percent": result[10],
            "rap_percent": result[11],
            "popularity_percent": result[12],
            "weird_percent": result[13],
            "is_legend": result[14],
            "folder": result[15],
            "series": result[16],
        }

        conn.close()
        return song
    else:
        pass  # TODO: Inhalte von automatischen Jobs laden


def update_job_song_by_id(job_id, song_id, song):
    """
    Bearbeitet einen Song eines Jobs anhand seiner ID

    :param job_id: ID des Jobs
    :param song_id: ID des Songs
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

    # Bearbeite den Song
    if manual:
        # Prüfe, ob es einen Song mit der ID in dem Job gibt
        c.execute(
            "SELECT id FROM excel_songs WHERE job_id = ? AND id = ?",
            (job_id, song_id),
        )
        result = c.fetchone()
        if result is None:
            conn.close()
            raise Exception("Song mit ID " + str(song_id) + " nicht gefunden")

        # Speichere die Änderungen
        c.execute(
            """UPDATE excel_songs SET title = ?, artists = ?, year = ?, language = ?, 
            length = ?, genre = ?, feels = ?, type = ?, speed = ?, voice_percent = ?, 
            rap_percent = ?, popularity_percent = ?, weird_percent = ?, is_legend = ?, 
            folder = ?, series = ? WHERE id = ?""",
            (
                song["title"],
                song["artists"],
                song["year"],
                song["language"],
                song["length"],
                song["genre"],
                song["feels"],
                song["type"],
                song["speed"],
                song["voice_percent"],
                song["rap_percent"],
                song["popularity_percent"],
                song["weird_percent"],
                song["is_legend"],
                song["folder"],
                song["series"],
                song_id,
            ),
        )

    else:
        pass  # TODO: Inhalte von automatischen Jobs bearbeiten

    conn.commit()
    conn.close()


def delete_job_song_by_id(job_id, song_id):
    """
    Löscht einen Song eines Jobs anhand seiner ID

    :param job_id: ID des Jobs
    :param song_id: ID des Songs
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

    # Lösche den Song
    if manual:
        # Prüfe, ob es einen Song mit der ID in dem Job gibt
        c.execute(
            "SELECT id FROM excel_songs WHERE job_id = ? AND id = ?",
            (job_id, song_id),
        )
        result = c.fetchone()
        if result is None:
            conn.close()
            raise Exception("Song mit ID " + str(song_id) + " nicht gefunden")

        # Lösche den Song aus der Tabelle excel_songs
        c.execute(
            "DELETE FROM excel_songs WHERE job_id = ? AND id = ?",
            (job_id, song_id),
        )
    else:
        pass  # TODO: Inhalte von automatischen Jobs löschen

    conn.commit()
    conn.close()


def create_playlist_from_job(job_id):
    """
    Überträgt die Songs eines Jobs in eine neue Playlist.
    Für den Zugriff auf TIDAL wird der TIDAL Account des Benutzers verwendet.
    Es wird eine neue Playlist erstellt und die Songs hinzugefügt.
    Dabei werden die Songs in TIDAL gesucht und die entsprechenden IDs gespeichert,
    die zugehörigen Künstler und Alben werden ebenfalls gespeichert.

    :param job_id: ID des Jobs
    :return: playlist_id
    :rtype: int
    """
    conn, c = open_database()

    # Importiere die Songs aus dem Job
    job = get_job_by_id(job_id)

    # Erstelle eine neue Playlist
    c.execute(
        """
        INSERT INTO playlists (name, created_at, created_by, updated_at, updated_by, manual)
        VALUES (?, CURRENT_TIMESTAMP, ?, CURRENT_TIMESTAMP, ?, ?)
        """,
        (job["name"], job["created_by"], job["updated_by"], job["manual"]),
    )
    playlist_id = c.lastrowid

    # Überprüfe, ob der aufrufende Benutzer ein TIDAL Account hat
    if current_user.tidal_session is None:
        conn.close()
        raise Exception("Benutzer hat keinen TIDAL Account verbunden")

    # Füge die Songs der Playlist hinzu
    for song in job["songs"]:
        # Suche den Song in TIDAL
        tidal_songs = current_user.tidal_session.search(
            query=f"{song['artists']} {song['title']}",
            limit=20,
            models=[tidalapi.media.Track],
        )

        # Überprüfe, ob mindestens ein Song gefunden wurde
        if tidal_songs["tracks"] is None or len(tidal_songs["tracks"]) == 0:
            print(
                f"Bei der ersten Sucher wurde für \"{song['artists']} {song['title']}\" keine Übereinstimmung gefunden"
            )

            # Versuche den Song mit einer anderen Suche zu finden (nur Titel)
            tidal_songs = current_user.tidal_session.search(
                query=f"{song['title']}",
                limit=50,
                models=[tidalapi.media.Track],
            )

            if tidal_songs["tracks"] is None or len(tidal_songs["tracks"]) == 0:
                print(
                    f"In einer zweiten Suche wurden keine Übereinstimmungen für \"{song['title']}\" gefunden"
                )
                continue  # Gehe zum nächsten Song aus der Job Liste
            else:
                print(
                    f"In einer zweiten Suche wurden Übereinstimmungen für \"{song['title']}\" gefunden"
                )
                # Durchsuche die Songs und wähle den richtigen Song aus

        # Wähle den richtigen Song aus den Suchergebnissen aus
        tidal_song = None

        for tidal_song_candidate in tidal_songs["tracks"]:
            # Überprüfe, ob der Titel und die Künstler grob übereinstimmen
            if (
                tidal_song_candidate.name.lower() in song["title"].lower()
                or song["title"].lower() in tidal_song_candidate.name.lower()
            ):
                # Titel kommen ineinander vor

                # Überprüfe, ob die Künstler grob übereinstimmen
                all_artists_match = True
                for artist in tidal_song_candidate.artists:
                    if artist.name.lower() in song["artists"].lower():
                        # Titel und Künstler stimmen überein
                        continue
                    else:
                        all_artists_match = False
                        break

                if all_artists_match:
                    # Titel und Künstler stimmen überein
                    tidal_song = tidal_song_candidate
                    print(
                        f'Song "{tidal_song.name}" wurde als Übereinstimmung gefunden'
                    )
                    break

        if tidal_song is None:
            # Kein Song wurde gefunden, obwohl die Suche mindestens einen Song zurückgegeben hat
            print(
                f"Es wurde trotz Suchergebnissen kein Song für \"{song['title']}\" gefunden"
            )
            continue

        # tidal_song = tidal_songs["tracks"][0] # Alternativ: Nimm den ersten Song aus der Liste

        # Überprüfe, ob der Song bereits in der Datenbank vorhanden ist
        c.execute(
            "SELECT id FROM songs WHERE tidal_id = ?",
            (tidal_song.id,),
        )
        song_id = c.fetchone()
        if song_id is not None:
            # Song ist bereits vorhanden, füge den Song der Playlist hinzu
            c.execute(
                "INSERT INTO playlist_song (playlist_id, song_id) VALUES (?, ?)",
                (playlist_id, song_id[0]),
            )
            continue

        # Song ist noch nicht vorhanden, erstelle den Song

        # Finde die IDs heraus, welche beim Song gespeichert werden müssen

        # Wenn kein Typ angegeben ist, dann setze den Typ auf "Unbekannt"
        if song["type"] is None:
            song["type"] = "Unbekannt"

        c.execute(
            "SELECT id FROM types WHERE name = ?",
            (song["type"],),
        )
        type_id = c.fetchone()
        if type_id is None:
            # Typ ist noch nicht vorhanden, erstelle den Typ
            c.execute(
                "INSERT INTO types (name) VALUES (?)",
                (song["type"],),
            )
            type_id = c.lastrowid
        else:
            type_id = type_id[0]

        c.execute(
            "SELECT id FROM albums WHERE tidal_id = ?",
            (tidal_song.album.id,),
        )
        album_id = c.fetchone()
        if album_id is None:
            c.execute(
                """INSERT INTO albums (title, release_date, tidal_id, tidal_cover) 
                VALUES (?, ?, ?, ?)""",
                (
                    tidal_song.album.name,
                    tidal_song.album.release_date.isoformat(),  # nutze ISO 8601 Format für Datum
                    tidal_song.album.id,
                    tidal_song.album.cover,
                ),
            )
            album_id = c.lastrowid
        else:
            album_id = album_id[0]

        # Speichere den Song in der Datenbank
        c.execute(
            """INSERT INTO songs (title, duration, explicit, type_id, voice_percent, rap_percent, popularity_percent, weird_percent,
             isrc, popularity_tidal, tidal_id, album_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                tidal_song.name,
                tidal_song.duration,
                tidal_song.explicit,
                type_id,
                song["voice_percent"],
                song["rap_percent"],
                song["popularity_percent"],
                song["weird_percent"],
                tidal_song.isrc,
                tidal_song.popularity,
                tidal_song.id,
                album_id,
            ),
        )
        song_id = c.lastrowid

        # Füge den Song zur Playlist hinzu
        c.execute(
            "INSERT INTO playlist_song (playlist_id, song_id) VALUES (?, ?)",
            (playlist_id, song_id),
        )

        # Künstler speichern
        for artist in tidal_song.artists:
            c.execute(
                "SELECT id FROM artists WHERE tidal_id = ?",
                (artist.id,),
            )
            artist_id = c.fetchone()
            if artist_id is None:
                # Künstler ist noch nicht vorhanden, erstelle den Künstler
                c.execute(
                    """INSERT INTO artists (name, tidal_id, tidal_cover, tidal_bio)
                    VALUES (?, ?, ?, ?)""",
                    (artist.name, artist.id, artist.picture, artist.bio),
                )
                artist_id = c.lastrowid
            else:
                artist_id = artist_id[0]

            # Überprüfe, ob die Rolle des Künstlers bereits vorhanden ist
            for role in artist.roles:
                c.execute(
                    "SELECT id FROM artist_roles WHERE name = ?",
                    (role.name,),
                )
                role_id = c.fetchone()
                if role_id is None:
                    # Rolle ist noch nicht vorhanden, erstelle die Rolle
                    c.execute(
                        "INSERT INTO artist_roles (name) VALUES (?)",
                        (role.name,),
                    )
                    role_id = c.lastrowid
                else:
                    role_id = role_id[0]

                # Verknüpfe den Künstler mit der Rolle und dem Song
                c.execute(
                    "INSERT INTO song_artist (song_id, artist_id, role_id) VALUES (?, ?, ?)",
                    (song_id, artist_id, role_id),
                )

        # Sprachen speichern, falls vorhanden
        if song["language"] is not None:
            for language in song["language"].split(", "):
                # Finde die Sprachen-ID heraus
                c.execute(
                    "SELECT id FROM languages WHERE name = ?",
                    (language,),
                )
                language_id = c.fetchone()
                if language_id is None:
                    # Sprache ist noch nicht vorhanden, erstelle die Sprache
                    c.execute(
                        "INSERT INTO languages (name) VALUES (?)",
                        (language,),
                    )
                    language_id = c.lastrowid
                else:
                    language_id = language_id[0]

                # Füge die Sprache dem Song hinzu
                c.execute(
                    "INSERT INTO language_song (song_id, language_id) VALUES (?, ?)",
                    (song_id, language_id),
                )

        # Genre speichern, falls vorhanden
        if song["genre"] is not None:
            # Finde die Genre-ID heraus
            c.execute(
                "SELECT id FROM genres WHERE name = ?",
                (song["genre"],),
            )
            genre_id = c.fetchone()
            if genre_id is None:
                # Genre ist noch nicht vorhanden, erstelle das Genre
                c.execute(
                    "INSERT INTO genres (name) VALUES (?)",
                    (song["genre"],),
                )
                genre_id = c.lastrowid
            else:
                genre_id = genre_id[0]

            # Füge das Genre dem Song hinzu
            c.execute(
                "INSERT INTO genre_song (song_id, genre_id) VALUES (?, ?)",
                (song_id, genre_id),
            )

        # Feels speichern, falls vorhanden
        if song["feels"] is not None:
            # Finde die Feels-ID heraus
            c.execute(
                "SELECT id FROM feels WHERE name = ?",
                (song["feels"],),
            )
            feels_id = c.fetchone()
            if feels_id is None:
                # Feels ist noch nicht vorhanden, erstelle das Feels
                c.execute(
                    "INSERT INTO feels (name) VALUES (?)",
                    (song["feels"],),
                )
                feels_id = c.lastrowid
            else:
                feels_id = feels_id[0]

            # Füge das Feels dem Song hinzu
            c.execute(
                "INSERT INTO feel_song (song_id, feel_id) VALUES (?, ?)",
                (song_id, feels_id),
            )

        # Speed speichern, falls vorhanden
        if song["speed"] is not None:
            # Finde die Speed-ID heraus
            c.execute(
                "SELECT id FROM speeds WHERE name = ?",
                (song["speed"],),
            )
            speed_id = c.fetchone()
            if speed_id is None:
                # Speed ist noch nicht vorhanden, erstelle das Speed
                c.execute(
                    "INSERT INTO speeds (name) VALUES (?)",
                    (song["speed"],),
                )
                speed_id = c.lastrowid
            else:
                speed_id = speed_id[0]

            # Füge das Speed dem Song hinzu
            c.execute(
                "INSERT INTO speed_song (song_id, speed_id) VALUES (?, ?)",
                (song_id, speed_id),
            )

        # Folder speichern, falls vorhanden
        if song["folder"] is not None:
            # Finde die Folder-ID heraus
            c.execute(
                "SELECT id FROM folders WHERE name = ?",
                (song["folder"],),
            )
            folder_id = c.fetchone()
            if folder_id is None:
                # Folder ist noch nicht vorhanden, erstelle den Folder
                c.execute(
                    "INSERT INTO folders (name) VALUES (?)",
                    (song["folder"],),
                )
                folder_id = c.lastrowid
            else:
                folder_id = folder_id[0]

            # Füge den Folder dem Song hinzu
            c.execute(
                "INSERT INTO folder_song (song_id, folder_id) VALUES (?, ?)",
                (song_id, folder_id),
            )

        # Series speichern, falls vorhanden
        if song["series"] is not None:
            # Finde die Series-ID heraus
            c.execute(
                "SELECT id FROM series WHERE name = ?",
                (song["series"],),
            )
            series_id = c.fetchone()
            if series_id is None:
                # Series ist noch nicht vorhanden, erstelle die Series
                c.execute(
                    "INSERT INTO series (name) VALUES (?)",
                    (song["series"],),
                )
                series_id = c.lastrowid
            else:
                series_id = series_id[0]

            # Füge die Series dem Song hinzu
            c.execute(
                "INSERT INTO series_song (song_id, series_id) VALUES (?, ?)",
                (song_id, series_id),
            )

    # Speichere alle Änderungen
    conn.commit()
    conn.close()


def get_playlists_by_user_id(user_id):
    """
    Gibt eine Liste mit Playlists zurück, die zu einem Benutzer gehören

    :param user_id: ID des Benutzers
    :return: Liste mit Playlists
    :rtype: list
    """
    conn, c = open_database()

    c.execute(
        """
        SELECT playlists.id, playlists.name, playlists.created_at, created_by.username,
        playlists.updated_at, updated_by.username, playlists.manual FROM playlists
        JOIN users AS created_by ON playlists.created_by = created_by.id
        JOIN users AS updated_by ON playlists.updated_by = updated_by.id
        WHERE created_by.id = ?
        """,
        (user_id,),
    )
    result = c.fetchall()
    if result is None:
        conn.close()
        return None
    playlists = []
    for row in result:
        playlists.append(
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
    return playlists


def get_playlist_by_id(playlist_id):
    """
    Gibt eine Playlist anhand ihrer ID zurück

    :param playlist_id: ID der Playlist
    :return: Playlist
    :rtype: dict
    """
    conn, c = open_database()

    # Überprüfe, ob es die Playlist gibt
    c.execute(
        """
        SELECT playlists.id, playlists.name, playlists.created_at, created_by.username,
        playlists.updated_at, updated_by.username, playlists.manual FROM playlists
        JOIN users AS created_by ON playlists.created_by = created_by.id
        JOIN users AS updated_by ON playlists.updated_by = updated_by.id
        WHERE playlists.id = ?
        """,
        (playlist_id,),
    )
    result = c.fetchone()
    if result is None:
        conn.close()
        raise Exception("Playlist mit ID " + str(playlist_id) + " nicht gefunden")

    playlist = {
        "id": result[0],
        "name": result[1],
        "created_at": result[2],
        "created_by": result[3],
        "updated_at": result[4],
        "updated_by": result[5],
        "manual": result[6],
    }

    # Lade die Songs der Playlist
    c.execute(
        """
        SELECT songs.id, songs.title, songs.duration, songs.explicit, types.name, songs.voice_percent,
        songs.rap_percent, songs.popularity_percent, songs.isrc, songs.weird_percent, songs.popularity_tidal, 
        songs.tidal_id, albums.title, albums.release_date, albums.tidal_id, albums.tidal_cover FROM playlist_song
        JOIN songs AS songs ON playlist_song.song_id = songs.id
        JOIN types AS types ON songs.type_id = types.id
        JOIN albums AS albums ON songs.album_id = albums.id
        WHERE playlist_song.playlist_id = ?
        """,
        (playlist_id,),
    )
    result = c.fetchall()
    if result is None:
        # Es gibt keine Songs in der Playlist, gebe eine leere Liste zurück
        conn.close()
        return playlist

    songs = []
    for row in result:
        # Finde die Künstler des Songs mit ihren Rollen heraus
        c.execute(
            """
            SELECT artists.name, artists.tidal_id, artists.tidal_cover, artists.tidal_bio,
            artist_roles.name FROM song_artist
            JOIN artists AS artists ON song_artist.artist_id = artists.id
            JOIN artist_roles AS artist_roles ON song_artist.role_id = artist_roles.id
            WHERE song_artist.song_id = ?
            """,
            (row[0],),
        )
        artists = c.fetchall()
        if artists is None:
            artists = []
        else:
            artists = [
                {
                    "name": artist[0],
                    "tidal_id": artist[1],
                    "tidal_cover": artist[2],
                    "tidal_bio": artist[3],
                    "role": artist[4],
                }
                for artist in artists
            ]

        # Finde die Sprachen des Songs heraus
        c.execute(
            """
            SELECT languages.name FROM language_song
            JOIN languages AS languages ON language_song.language_id = languages.id
            WHERE language_song.song_id = ?
            """,
            (row[0],),
        )
        languages = c.fetchall()
        if languages is None:
            languages = []
        else:
            languages = [
                {
                    "name": language[0],
                }
                for language in languages
            ]

        # Finde die Genres des Songs heraus
        c.execute(
            """
            SELECT genres.name FROM genre_song
            JOIN genres AS genres ON genre_song.genre_id = genres.id
            WHERE genre_song.song_id = ?
            """,
            (row[0],),
        )
        genres = c.fetchall()
        if genres is None:
            genres = []
        else:
            genres = [
                {
                    "name": genre[0],
                }
                for genre in genres
            ]

        # Finde die Feels des Songs heraus
        c.execute(
            """
            SELECT feels.name FROM feel_song
            JOIN feels AS feels ON feel_song.feel_id = feels.id
            WHERE feel_song.song_id = ?
            """,
            (row[0],),
        )
        feels = c.fetchall()
        if feels is None:
            feels = []
        else:
            feels = [
                {
                    "name": feel[0],
                }
                for feel in feels
            ]

        # Finde die Speeds des Songs heraus
        c.execute(
            """
            SELECT speeds.name FROM speed_song
            JOIN speeds AS speeds ON speed_song.speed_id = speeds.id
            WHERE speed_song.song_id = ?
            """,
            (row[0],),
        )
        speeds = c.fetchall()
        if speeds is None:
            speeds = []
        else:
            speeds = [
                {
                    "name": speed[0],
                }
                for speed in speeds
            ]

        # Finde die Folder des Songs heraus
        c.execute(
            """
            SELECT folders.name FROM folder_song
            JOIN folders AS folders ON folder_song.folder_id = folders.id
            WHERE folder_song.song_id = ?
            """,
            (row[0],),
        )
        folders = c.fetchall()
        if folders is None:
            folders = []
        else:
            folders = [
                {
                    "name": folder[0],
                }
                for folder in folders
            ]

        # Finde die Series des Songs heraus
        c.execute(
            """
            SELECT series.name FROM series_song
            JOIN series AS series ON series_song.series_id = series.id
            WHERE series_song.song_id = ?
            """,
            (row[0],),
        )
        series = c.fetchall()
        if series is None:
            series = []
        else:
            series = [
                {
                    "name": serie[0],
                }
                for serie in series
            ]

        songs.append(
            {
                "id": row[0],
                "title": row[1],
                "duration": row[2],
                "explicit": row[3],
                "type": row[4],
                "voice_percent": row[5],
                "rap_percent": row[6],
                "popularity_percent": row[7],
                "isrc": row[8],
                "weird_percent": row[9],
                "popularity_tidal": row[10],
                "tidal_id": row[11],
                "album": {
                    "title": row[12],
                    "release_date": row[13],
                    "tidal_id": row[14],
                    "tidal_cover": row[15],
                },
                "artists": artists,
                "languages": languages,
                "genres": genres,
                "feels": feels,
                "speeds": speeds,
                "folders": folders,
                "series": series,
            }
        )

    playlist["songs"] = songs

    conn.close()
    return playlist


def delete_playlist_by_id(playlist_id):
    """
    Löscht eine Playlist anhand ihrer ID

    :param playlist_id: ID der Playlist
    :return: None
    """
    pass


def edit_playlist_by_id(playlist_id, settings):
    """
    Bearbeitet eine Playlist anhand ihrer ID

    :param playlist_id: ID der Playlist
    :param settings: Einstellungen für die Playlist
    :return: None
    """
    pass


def add_tidal_user_token(user_id, tidal_token):
    """
    Fügt einen TIDAL-Token zu einem Benutzer hinzu

    :param user_id: ID des Benutzers
    :param tidal_token: TIDAL-Token (access_token, refresh_token, expiry_time, token_type)
    :return: None
    """
    conn, c = open_database()

    # Überprüfe, ob der Benutzer bereits einen TIDAL-Account hat,
    # falls ja, dann aktualisiere den Token und die Ablaufzeit des Tokens
    c.execute(
        "SELECT tidal_account_id FROM users WHERE id = ?",
        (user_id,),
    )
    tidal_account_id = c.fetchone()[0]
    if tidal_account_id is not None:
        # Aktualisiere den Token und die Ablaufzeit des Tokens
        c.execute(
            "UPDATE tidal_credentials SET token_type = ?, access_token = ?, refresh_token = ?, expiry_time = ? WHERE id = ?",
            (
                tidal_token["token_type"],
                tidal_token["access_token"],
                tidal_token["refresh_token"],
                tidal_token["expiry_time"].timestamp(),
                tidal_account_id,
            ),
        )
    # Falls der Benutzer noch keinen TIDAL-Account hat, dann erstelle einen neuen
    else:
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
