from flask import render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user

from app.songs import bp
from app.extensions import db
from app.models.song import Song



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


    
