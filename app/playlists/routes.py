from flask import render_template, redirect, url_for, request, jsonify, flash, abort
from flask_login import login_required, current_user
from flask_sqlalchemy import SQLAlchemy


from app.playlists import bp
from app.extensions import db
from app.models.playlist import Playlist, song_playlist
from app.models.job import Job
from app.models.song import Song


@bp.route("/playlists")
@login_required
def index():
    return render_template(
        "playlists.html", playlists=Playlist.query.filter_by(created_by=current_user.id)
    )


@bp.route("/playlists/create?job_id=<int:job_id>", methods=["GET"])
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


@bp.route("/playlists/<int:playlist_id>", methods=["GET"])
@login_required
def playlist_details(playlist_id):

    # Load additional query parameters from the URL
    page = request.args.get("page", 1, type=int)

    # Exception handling for invalid arguments
    if page < 1:  # In this case we save a query to the database
        abort(404)  # TODO: Implement a custom error page

    # TODO: Validate the playlist_id and if the user has access to it

    # Get the playlist and the songs, but only 50 songs at a time
    playlist = Playlist.query.filter_by(id=playlist_id).first()
    songs = (
        Song.query.join(song_playlist)
        .filter(song_playlist.c.playlist_id == playlist_id)
        .paginate(page=page, per_page=50, error_out=False)
    )

    # Validate whether the page exists
    if page > songs.pages:
        abort(404)

    # with songs.has_prev and songs.has_next we can check if there are more songs,
    # and with songs.prev_num and songs.next_num we can get the page number.
    # We can use this information to create a pagination in the template.
    return render_template("playlist.html", playlist=playlist, songs=songs)


@bp.route("/playlists/<int:playlist_id>", methods=["DELETE"])
@login_required
def playlist_delete(playlist_id):
    playlist = Playlist.query.filter_by(id=playlist_id).first()
    db.session.delete(playlist)
    db.session.commit()

    return jsonify({"success": True})


@bp.route("/playlists/<int:playlist_id>/refresh", methods=["PATCH"])
@login_required
def playlist_refresh(playlist_id):
    """
    Refreshes the song data for each song in playlist from TIDAL
    """
    playlist = Playlist.query.filter_by(id=playlist_id).first()
    success = None
    try:
        for song in playlist.songs:
            # Only search for songs that have not been found in TIDAL yet
            if song.tidal_song_id is None:
                song.search_in_tidal()

        return jsonify({"success": True})
    except Exception as e:
        print(e)
        return jsonify({"success": False})


@bp.route("/playlists/<int:playlist_id>/songs/<int:song_id>", methods=["DELETE"])
@login_required
def playlist_song_delete(playlist_id, song_id):
    playlist = Playlist.query.filter_by(id=playlist_id).first()
    song = Song.query.filter_by(id=song_id).first()

    if song in playlist.songs:
        try:
            playlist.songs.remove(song)
            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            print(e)
            return jsonify({"success": False, "error": str(e)})
    else:
        return jsonify({"success": False, "error": "Song not in playlist"})


# Export the playlist to TIDAL (Create a playlist in TIDAL and add the songs)
@bp.route("/playlists/<int:playlist_id>/export", methods=["POST"])
@login_required
def playlist_export(playlist_id):
    playlist = Playlist.query.filter_by(id=playlist_id).first()
    try:
        playlist = playlist.export_to_tidal(current_user)

        url = f"https://listen.tidal.com/playlist/{playlist.id}"

        return jsonify({"success": True, "url": url})
    except Exception as e:
        print(e)
        return jsonify({"success": False, "error": str(e)})