from flask import render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user

from app.songs import bp
from app.extensions import db
from app.models.song import Song, Tag, Genre, Feel, Speed, Folder, Series



@bp.route("/song/<int:song_id>/refresh", methods=["PATCH"])
@login_required
def refresh_song(song_id):
    """
    Refreshes the song data from TIDAL
    """
    song = Song.query.filter_by(id=song_id).first()
    success = None
    try:
        song.search_in_tidal()
        success = True
    except Exception as e:
        print(e)
        success = False
    
    response = {"success": success}
    return jsonify(response)


@bp.route("/song/<int:song_id>/tag/<string:tag_type>/<int:tag_id>", methods=["DELETE"])
@login_required
def song_tag_delete(song_id, tag_type, tag_id):
    song = Song.query.filter_by(id=song_id).first()

    if tag_type == "genre":
        tag = Genre.query.filter_by(id=tag_id).first()
        song.genres.remove(tag)
    elif tag_type == "feel":
        tag = Feel.query.filter_by(id=tag_id).first()
        song.feels.remove(tag)
    elif tag_type == "speed":
        tag = Speed.query.filter_by(id=tag_id).first()
        song.speeds.remove(tag)
    elif tag_type == "tag":
        tag = Tag.query.filter_by(id=tag_id).first()
        song.tags.remove(tag)
    elif tag_type == "folder":
        tag = Folder.query.filter_by(id=tag_id).first()
        song.folders.remove(tag)
    elif tag_type == "serie":
        tag = Series.query.filter_by(id=tag_id).first()
        song.series.remove(tag)
    else:
        return jsonify({"success": False})
    
    db.session.commit()
    return jsonify({"success": True})

    
