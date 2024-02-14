from datetime import datetime

import tidalapi

from app.extensions import db

song_playlist = db.Table(
    "song_playlist",
    db.Column("song_id", db.Integer, db.ForeignKey("songs.id"), primary_key=True),
    db.Column(
        "playlist_id", db.Integer, db.ForeignKey("playlists.id"), primary_key=True
    ),
)

class Playlist(db.Model):
    __tablename__ = "playlists"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), index=True, nullable=False)
    created_at = db.Column(
        db.DateTime, index=True, nullable=False, default=datetime.now()
    )
    updated_at = db.Column(
        db.DateTime, index=True, nullable=False, default=datetime.now()
    )
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    manual = db.Column(db.Boolean, default=False, nullable=False)

    songs = db.relationship("Song", secondary=song_playlist, backref="Playlist", lazy="dynamic")

    def __repr__(self):
        return f"<Playlist {self.name}>"

    def __init__(self, name, created_by, manual=False):
        self.name = name
        self.created_by = created_by
        self.updated_by = created_by
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.manual = manual

    def convert_job_to_playlist(self, job):
        for song in job.songs:
            self.songs.append(song)
        db.session.add(self)
        db.session.commit()
