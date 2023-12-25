# music.py

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from flask import request, redirect, url_for, flash

from database import get_jobs_by_user_id, delete_job_by_id, get_job_by_id, import_excel_songs_manually, get_playlist_by_id

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
    return render_template("job-details.html", job=get_job_by_id(job_id))

@music.route("/job/<int:job_id>", methods=["PATCH"])
@login_required
def job_edit(job_id):
    # TODO: Job-Details anzeigen implementieren
    return render_template("job.html", job_id=job_id)


@music.route("/job/<int:job_id>", methods=["DELETE"])
@login_required
def job_delete(job_id):
    delete_job_by_id(job_id)
    return redirect(url_for("music.jobs"))




@music.route("/playlists")
@login_required
def playlists():
    return render_template("playlists.html")


@music.route("/playlist/create", methods=["POST"])
@login_required
def playlist_create(playlist_id):
    # TODO: Job erstellen implementieren
    return render_template("playlist.html", playlist_id=playlist_id)

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




