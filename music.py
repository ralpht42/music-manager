# music.py

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from flask import request, redirect, url_for, flash, jsonify

from database import import_excel_songs_manually, get_job_by_id
from database import get_jobs_by_user_id, delete_job_by_id
from database import get_job_song_by_id, update_job_song_by_id, delete_job_song_by_id
from database import (
    create_playlist_from_job,
    get_playlists_by_user_id,
    get_playlist_by_id,
    delete_playlist_by_id,
)

music = Blueprint("music", __name__)


@music.route("/jobs")
@login_required
def jobs():
    return render_template("jobs.html", jobs=get_jobs_by_user_id(current_user.id))


@music.route("/job/upload_file", methods=["POST"])
@login_required
def job_upload_file():
    if "song_excel_file" not in request.files:
        flash("Keine Excel-Datei hochgeladen")
        return redirect(url_for("music.jobs"))
    file = request.files["song_excel_file"]
    if file.filename == "":
        flash("Ungültige Datei hochgeladen")
        return redirect(url_for("music.jobs"))
    else:
        import_excel_songs_manually(file, current_user.id)
        return redirect(url_for("music.jobs"))


@music.route("/job/create", methods=["POST"])
@login_required
def job_create(job_id):
    # TODO: Job erstellen implementieren
    return render_template("job.html", job_id=job_id)


@music.route("/job/<int:job_id>", methods=["GET"])
@login_required
def job_details(job_id):
    return render_template("job.html", job=get_job_by_id(job_id))


@music.route("/job/<int:job_id>", methods=["DELETE"])
@login_required
def job_delete(job_id):
    success = None
    try:
        delete_job_by_id(job_id)
        success = True
    except Exception as e:
        flash("Fehler beim Löschen des Jobs: " + str(e))
        success = False
    response = {"success": success}
    return jsonify(response)


@music.route("/job/<int:job_id>/song/<int:song_id>", methods=["GET"])
@login_required
def job_song_details(job_id, song_id):
    return render_template(
        "job_song.html",
        song=get_job_song_by_id(job_id, song_id),
        job=get_job_by_id(job_id),
    )


@music.route("/job/<int:job_id>/song/<int:song_id>", methods=["POST"])
@login_required
def job_song_update(job_id, song_id):
    song = {
        "title": request.form.get("title"),  # Jeder Song braucht einen Titel
        "artists": request.form.get("artists") or None,
        "year": request.form.get("year") or None,
        "language": request.form.get("language") or None,
        "length": request.form.get("length") or None,
        "genre": request.form.get("genre") or None,
        "feels": request.form.get("feels") or None,
        "type": request.form.get("type") or None,
        "speed": request.form.get("speed") or None,
        "voice_percent": request.form.get("voice_percent") or None,
        "rap_percent": request.form.get("rap_percent") or None,
        "popularity_percent": request.form.get("popularity_percent") or None,
        "weird_percent": request.form.get("weird_percent") or None,
        "is_legend": request.form.get("is_legend") or None,
        "folder": request.form.get("folder") or None,
        "series": request.form.get("series") or None,
        "song_id": song_id,
    }

    update_job_song_by_id(job_id, song_id, song)
    return render_template(
        "job_song.html",
        song=get_job_song_by_id(job_id, song_id),
        job=get_job_by_id(job_id),
    )


@music.route("/job/<int:job_id>/song/<int:song_id>", methods=["DELETE"])
@login_required
def job_song_delete(job_id, song_id):
    success = None
    try:
        delete_job_song_by_id(job_id, song_id)
        success = True
    except Exception as e:
        flash("Fehler beim Löschen des Songs: " + str(e))
        success = False
    response = {"success": success}

    return jsonify(response)


@music.route("/playlists")
@login_required
def playlists():
    return render_template(
        "playlists.html", playlists=get_playlists_by_user_id(current_user.id)
    )


@music.route("/playlist/create", methods=["POST"])
@login_required
def playlist_create(job_id=None):
    # TODO: Implementieren

    # Wenn ein Job ausgewählt wurde, dann die ID des Jobs auslesen
    # und den Inhalt der Playlist mit den Songs des Jobs füllen
    if "job_id" in request.form:
        job_id = request.form.get("job_id")

        create_playlist_from_job(job_id)
        return redirect(url_for("music.playlists"))
    else:
        # TODO: Leere Playlist erstellen implementieren
        return redirect(url_for("music.playlists"))


@music.route("/playlist/<int:playlist_id>", methods=["GET"])
@login_required
def playlist_details(playlist_id):
    return render_template("playlist.html", playlist=get_playlist_by_id(playlist_id))


@music.route("/playlist/<int:playlist_id>", methods=["PATCH"])
@login_required
def playlist_edit(playlist_id):
    return render_template("playlist.html", playlist_id=playlist_id)


@music.route("/playlist/<int:playlist_id>", methods=["DELETE"])
@login_required
def playlist_delete(playlist_id):
    return redirect(url_for("music.playlists"))
