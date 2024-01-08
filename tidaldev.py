"""
Dieses Modul ist aufgrund von Limitierungen der TIDAL-API als veraltet zu betrachten.
Zukünftige Entwicklungen werden mit der TIDAL-API nicht fortgesetzt. 
Stattdessen ist das pypy-Modul tidalapi zu verwenden. 
Darüber authentifieren sich Benutzer bei TIDAL und nicht die Anwendung.
Bei diesem Vorgehen wurden bisher keine Limitierungen festgestellt.
"""


import base64
import requests

from flask import Flask, current_app
from datetime import datetime

import json


def refresh_tidal_app_token():
    """
    Diese Funktion sendet eine Anfrage an die TIDAL-API, um einen Zugriffstoken zu erhalten.

    :return: Ein Diktionär mit dem Zugriffstoken, dem Token-Typ und der Ablaufzeit des Tokens.
    """
    client_id = current_app.config["TIDAL_APP_CLIENT_ID"]
    client_secret = current_app.config["TIDAL_APP_CLIENT_SECRET"]

    if client_id is None or client_secret is None:
        raise Exception(
            "TIDAL_APP_CLIENT_ID oder TIDAL_APP_CLIENT_SECRET nicht gesetzt."
        )

    # Erstelle die Basis-64-Codierung von CLIENT_ID und CLIENT_SECRET
    credentials = base64.b64encode(
        f"{client_id}:{client_secret}".encode("utf-8")
    ).decode("utf-8")

    # Definiere die URL und die Header für die Anfrage
    url = "https://auth.tidal.com/v1/oauth2/token"
    headers = {"Authorization": f"Basic {credentials}"}

    # Definiere die Daten für die Anfrage
    data = {"grant_type": "client_credentials"}

    # Sende die Anfrage und erhalte die Antwort
    response = requests.post(url, headers=headers, data=data)

    # Überprüfen Sie den Statuscode der Antwort
    if response.status_code == 200:
        # Wenn die Anfrage erfolgreich war, geben Sie den Zugriffstoken zurück
        response_json = response.json()
        response_json["expiry_time"] = response_json["expires_in"] + int(
            datetime.now().timestamp()
        )
        current_app.config["TIDAL_APP_TOKEN"] = response_json
    else:
        # Wenn die Anfrage fehlgeschlagen ist, geben Sie eine Fehlermeldung zurück
        raise Exception(
            f"Es der Fehlercode {response.status_code} beim Aktualisieren des TIDAL-App-Tokens aufgetreten."
        )


# BUG: Das Rate Limit von TIDAL wird nicht beachtet, daher können keine größeren Mengen an Daten abgerufen werden
def search(type, query):
    """
    Diese Funktion sendet eine Anfrage an die TIDAL-API, um nach Songs zu suchen.

    :param type: Der Typ der Suche (ARTISTS, ALBUMS, TRACKS, VIDEOS)
    :param query: Der Suchbegriff
    :return: Ein Diktionär mit den Suchergebnissen
    """

    # Überprüfe ob die Anwendung mit TIDAL verbunden ist
    if current_app.config["TIDAL_APP_TOKEN"] is None:
        raise Exception("Die Anwendung ist nicht mit TIDAL verbunden.")

    # Überprüfen Sie, ob der Token abgelaufen ist
    if (
        current_app.config["TIDAL_APP_TOKEN"]["expiry_time"]
        < datetime.now().timestamp() + 60
    ):
        # Wenn der Token abgelaufen ist, aktualisiere den Token
        refresh_tidal_app_token()

    # Definiere die URL und die Header für die Anfrage
    url = "https://openapi.tidal.com/search"
    headers = {
        "Authorization": f"Bearer {current_app.config['TIDAL_APP_TOKEN']['access_token']}",
        "accept": "application/vnd.tidal.v1+json",
        "Content-Type": "application/vnd.tidal.v1+json",
    }

    params = {
        "query": query,
        "type": type,  # ALBUMS, ARTISTS, TRACKS, VIDEOS
        "offset": 0,  # Offset der Suchergebnisse,
        "limit": 10,  # Anzahl der Suchergebnisse
        "countryCode": "DE",  # ISO 3166-1 alpha-2 country code, z.B. DE, AT, CH, US TODO: Abhängig vom persönlichen TIDAL-Account des Benutzers machen
        "popularity": "WORLDWIDE",  # WORLDWIDE, COUNTRY
    }

    # Sende die Anfrage und erhalte die Antwort
    response = requests.get(url, headers=headers, params=params)

    # Überprüfen Sie den Statuscode der Antwort
    if response.status_code == 207:
        # Im folgenden wird "tracks" als Beispiel verwendet, da die Struktur für alle Suchergebnisse gleich ist,
        # d. h. "tracks", "albums", "artists" und "videos" haben im wesentlichen die gleiche Struktur.

        response_json = json.loads(response.text)

        # Wenn die Anfrage erfolgreich war, filtere nur die erfolgreichen Suchergebnisse
        for track in response_json[type.lower()]:
            if track["status"] != 200:
                # Wenn der Status nicht 200 ist, dann entferne den Track aus der Liste
                response_json[type.lower()].remove(track)
            else:
                track.update(track["resource"])
                del track["resource"]
                del track["status"]
                del track["message"]

        # Wenn die Anfrage erfolgreich war, geben Sie die Suchergebnisse zurück
        return response_json[type.lower()]
    else:
        # Wenn die Anfrage fehlgeschlagen ist, geben Sie eine Fehlermeldung zurück
        print(
            f"Es der Fehlercode { response.status_code } beim Suchen von { query } aufgetreten."
        )
        return None
