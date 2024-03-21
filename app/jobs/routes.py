from flask import Blueprint, render_template
from flask_login import login_required, current_user
from flask import request, redirect, url_for, flash, jsonify
from datetime import datetime

from app.extensions import db
from app.models.job import Job, song_job
from app.models.song import Song

from app.jobs import bp


@bp.route("/jobs")
@login_required
def index():
    jobs = Job.query.filter_by(created_by=current_user.id).all()
    return render_template("jobs.html", jobs=jobs)


@bp.route("/job/upload_file", methods=["POST"])
@login_required
def job_upload_file():
    if "song_excel_file" not in request.files:
        flash("Keine Excel-Datei hochgeladen")
        return redirect(url_for("jobs.index"))
    file = request.files["song_excel_file"]
    if file.filename == "":
        flash("Ungültige Datei hochgeladen")
        return redirect(url_for("jobs.index"))
    else:
        # Erstellen eines neuen Jobs und Importieren der Excel-Datei
        # Der Job wird dabei nach der Datei benannt und als manuell markiert

        job = Job(
            name=f"Job {file.filename} von {current_user.username} am {datetime.now().strftime('%d.%m.%Y um %H:%M:%S')}",
            created_by=current_user.id,
            manual=True,
        )
        db.session.add(job)
        db.session.commit()

        job.import_excel_file(file)

        return redirect(url_for("jobs.index"))


@bp.route("/job/create", methods=["POST"])
@login_required
def job_create(job_id):
    # TODO: Job erstellen implementieren
    return render_template("job.html", job_id=job_id)


@bp.route("/job/<int:job_id>", methods=["GET"])
@login_required
def job_details(job_id):

    # Load additional query parameters from the URL
    page = request.args.get("page", 1, type=int)

    # Exception handling for invalid arguments
    if page < 1:  # In this case we save a query to the database
        abort(404)  # TODO: Implement a custom error page

    # TODO: Validate the job_id and if the user has access to it

    # Get the playlist and the songs, but only 50 songs at a time
    job = Job.query.filter_by(id=job_id).first()
    songs = (
        Song.query.join(song_job)
        .filter(song_job.c.job_id == job_id)
        .paginate(page=page, per_page=50, error_out=False)
    )

    # Validate whether the page exists
    if page > songs.pages:
        abort(404)

    return render_template("job.html", job=job, songs=songs)


@bp.route("/job/<int:job_id>", methods=["DELETE"])
@login_required
def job_delete(job_id):
    success = None
    try:
        # Löschen des Jobs, alle Songs bleiben erhalten
        db.session.query(song_job).filter_by(job_id=job_id).delete()
        Job.query.filter_by(id=job_id).delete()
        db.session.commit()
        success = True
    except Exception as e:
        flash("Fehler beim Löschen des Jobs: " + str(e))
        success = False
    response = {"success": success}
    return jsonify(response)


@bp.route("/job/<int:job_id>/song/<int:song_id>", methods=["GET"])
@login_required
def job_song_details(job_id, song_id):
    return render_template(
        "job_song.html",
        song=Song.query.filter_by(id=song_id).first(),
        job=Job.query.filter_by(id=job_id).first(),
    )


@bp.route("/job/<int:job_id>/song/<int:song_id>", methods=["POST"])
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
        # song=get_job_song_by_id(job_id, song_id), # TODO: Funktion implementieren
        job=Job.query.filter_by(id=job_id).first(),
    )


@bp.route("/job/<int:job_id>/song/<int:song_id>", methods=["DELETE"])
@login_required
def job_song_delete(job_id, song_id):
    success = None
    try:
        # Löschen der Verknüpfung zwischen Song und Job
        # Job und Song bleiben erhalten, da sie auch in anderen Jobs verwendet werden können
        db.session.query(song_job).filter_by(job_id=job_id, song_id=song_id).delete()
        db.session.commit()
        success = True
    except Exception as e:
        flash("Fehler beim Löschen des Songs: " + str(e))
        success = False
    response = {"success": success}

    return jsonify(response)
