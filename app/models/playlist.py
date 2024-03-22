from datetime import datetime

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

    songs = db.relationship(
        "Song", secondary=song_playlist, backref="Playlist", lazy="joined"
    )

    def __repr__(self):
        return f"<Playlist {self.name}>"

    def __init__(self, name, created_by, manual=False):
        self.name = name
        self.created_by = created_by
        self.updated_by = created_by
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.manual = manual
        self.tidal_playlist_id = None

    def convert_job_to_playlist(self, job):
        for song in job.songs:
            self.songs.append(song)
        db.session.add(self)
        db.session.commit()

    def export_to_tidal(self, current_user):
        """
        This method exports the playlist to TIDAL by creating a new playlist in TIDAL and adding the songs
        """

        if self.tidal_playlist_id is not None:
            raise Exception(
                f"Playlist {self.name} has already been exported to TIDAL. The TIDAL playlist ID is {self.tidal_playlist_id}"
            )

        if self.songs is None or len(self.songs) == 0:
            raise Exception("Playlist has no songs")

        songs_ids = [
            song.tidal_song_id for song in self.songs if song.tidal_song_id is not None
        ]

        if len(songs_ids) == 0:
            raise Exception(
                "None of the songs in the playlist have been found in TIDAL"
            )

        # Create the playlist in TIDAL
        tidal_playlist = current_user.tidal_session.user.create_playlist(
            self.name, "Playlist created by Music Manager"
        )
        # Split the songs in chunks of 100 songs to avoid TIDAL API limit
        for i in range(0, len(songs_ids), 100):
            tidal_playlist.add(songs_ids[i : i + 100])

        self.tidal_playlist_id = tidal_playlist.id

        return tidal_playlist
