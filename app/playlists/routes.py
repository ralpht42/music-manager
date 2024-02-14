from flask import render_template, redirect, url_for, request
from flask_login import login_required, current_user

from app.playlists import bp
from app.extensions import db
from app.models.playlist import Playlist, song_playlist
from app.models.job import Job


@bp.route("/playlists")
@login_required
def index():
    return render_template(
        "playlists.html", playlists=Playlist.query.filter_by(created_by=current_user.id)
    )


@bp.route("/playlist/create?job_id=<int:job_id>", methods=["GET"])
@login_required
def playlist_create(job_id):
    job = Job.query.filter_by(id=job_id).first()

    if job.created_by != current_user.id:
        flash(
            "Du kannst nur Playlists von Jobs erstellen, die du selbst erstellt hast."
        )
        return redirect(url_for("jobs.jobs"))

    playlist = Playlist(
        name="Playlist für Job {job_name} von {username}.".format(
            job_name=job.name, username=current_user.username
        ),
        created_by=current_user.id,
        manual=True,
    )
    db.session.add(playlist)
    db.session.commit()

    playlist.convert_job_to_playlist(job)
    db.session.commit()
    return redirect(url_for("playlists.index"))


@bp.route("/playlist/<int:playlist_id>", methods=["GET"])
@login_required
def playlist_details(playlist_id):
    return render_template(
        "playlist.html", playlist=Playlist.query.filter_by(id=playlist_id).first()
    )


@bp.route("/playlist/<int:playlist_id>", methods=["PATCH"])
@login_required
def playlist_edit(playlist_id):
    return render_template("playlist.html", playlist_id=playlist_id)


@bp.route("/playlist/<int:playlist_id>", methods=["DELETE"])
@login_required
def playlist_delete(playlist_id):
    return redirect(url_for("playlists.index"))
