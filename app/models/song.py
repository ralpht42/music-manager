from app.extensions import db


song_artist_role = db.Table(
    "song_artist_role",
    db.Column("song_id", db.Integer, db.ForeignKey("songs.id"), primary_key=True),
    db.Column("artist_id", db.Integer, db.ForeignKey("artists.id"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
)


song_language = db.Table(
    "song_language",
    db.Column("song_id", db.Integer, db.ForeignKey("songs.id"), primary_key=True),
    db.Column(
        "language_id", db.Integer, db.ForeignKey("languages.id"), primary_key=True
    ),
)


song_genre = db.Table(
    "song_genre",
    db.Column("song_id", db.Integer, db.ForeignKey("songs.id"), primary_key=True),
    db.Column("genre_id", db.Integer, db.ForeignKey("genres.id"), primary_key=True),
)

song_feel = db.Table(
    "song_feel",
    db.Column("song_id", db.Integer, db.ForeignKey("songs.id"), primary_key=True),
    db.Column("feel_id", db.Integer, db.ForeignKey("feels.id"), primary_key=True),
)

song_speed = db.Table(
    "song_speed",
    db.Column("song_id", db.Integer, db.ForeignKey("songs.id"), primary_key=True),
    db.Column("speed_id", db.Integer, db.ForeignKey("speeds.id"), primary_key=True),
)

song_folder = db.Table(
    "song_folder",
    db.Column("song_id", db.Integer, db.ForeignKey("songs.id"), primary_key=True),
    db.Column("folder_id", db.Integer, db.ForeignKey("folders.id"), primary_key=True),
)

song_series = db.Table(
    "song_series",
    db.Column("song_id", db.Integer, db.ForeignKey("songs.id"), primary_key=True),
    db.Column("series_id", db.Integer, db.ForeignKey("series.id"), primary_key=True),
)
song_tag = db.Table(
    "song_tag",
    db.Column("song_id", db.Integer, db.ForeignKey("songs.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id"), primary_key=True),
)


class Album(db.Model):
    __tablename__ = "albums"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60), index=True, nullable=False)
    tidal_album_id = db.Column(db.Integer, index=True, nullable=True)
    tidal_cover_url = db.Column(db.String(60), nullable=True)
    tidal_explicit = db.Column(db.Boolean, nullable=True)

    songs = db.relationship("Song", backref="Album", lazy="dynamic")

    def __repr__(self):
        return f"<Album {self.title}>"


class Artist(db.Model):
    __tablename__ = "artists"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), index=True, nullable=False)
    tidal_artist_id = db.Column(db.Integer, index=True, unique=True, nullable=True)
    tidal_cover_url = db.Column(db.String(60), nullable=True)

    songs = db.relationship(
        "Song", secondary=song_artist_role, back_populates="artists", lazy="dynamic"
    )

    def __init__(self, name, tidal_artist_id=None, tidal_cover_url=None):
        self.name = name
        self.tidal_artist_id = tidal_artist_id
        self.tidal_cover_url = tidal_cover_url

    def __repr__(self):
        return f"<Artist {self.name}>"

    def get_role_for_song(self, song):
        return (
            Role.query.join(song_artist_role)
            .join(Artist)
            .filter(song_artist_role.c.artist_id == self.id)
            .filter(song_artist_role.c.song_id == song.id)
            .first()
        )


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)

    def __repr__(self):
        return f"<Role {self.name}>"


class Song(db.Model):
    __tablename__ = "songs"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60), index=True, nullable=False)
    duration = db.Column(db.Integer, nullable=True)
    release_year = db.Column(db.Integer, nullable=True)

    type_id = db.Column(db.Integer, db.ForeignKey("songtypes.id"), nullable=True)
    album_id = db.Column(db.Integer, db.ForeignKey("albums.id"), nullable=True)

    voice_percent = db.Column(db.Integer, nullable=True)
    rap_percent = db.Column(db.Integer, nullable=True)
    popularity_percent = db.Column(db.Integer, nullable=True)
    weird_percent = db.Column(db.Integer, nullable=True)

    isrc = db.Column(db.String(12), nullable=True)
    tidal_song_id = db.Column(db.Integer, nullable=True)

    artists = db.relationship(
        "Artist", secondary=song_artist_role, back_populates="songs", lazy="dynamic"
    )

    languages = db.relationship(
        "Language", secondary=song_language, back_populates="songs", lazy="dynamic"
    )
    genres = db.relationship(
        "Genre", secondary=song_genre, back_populates="songs", lazy="dynamic"
    )
    feels = db.relationship(
        "Feel", secondary=song_feel, back_populates="songs", lazy="dynamic"
    )
    speeds = db.relationship(
        "Speed", secondary=song_speed, back_populates="songs", lazy="dynamic"
    )
    folders = db.relationship(
        "Folder", secondary=song_folder, back_populates="songs", lazy="dynamic"
    )
    series = db.relationship(
        "Series", secondary=song_series, back_populates="songs", lazy="dynamic"
    )
    tags = db.relationship(
        "Tag", secondary=song_tag, back_populates="songs", lazy="dynamic"
    )

    def __repr__(self):
        return f"<Song {self.title}>"

    def __init__(
        self,
        title,
        duration=None,
        explicit=None,
        type_id=None,
        album_id=None,
        voice_percent=None,
        rap_percent=None,
        popularity_percent=None,
        weird_percent=None,
        isrc=None,
        tidal_song_id=None,
    ):
        self.title = title
        self.duration = duration
        self.explicit = explicit
        self.type_id = type_id
        self.album_id = album_id
        self.voice_percent = voice_percent
        self.rap_percent = rap_percent
        self.popularity_percent = popularity_percent
        self.weird_percent = weird_percent
        self.isrc = isrc
        self.tidal_song_id = tidal_song_id


class SongType(db.Model):
    __tablename__ = "songtypes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), index=True, unique=True, nullable=False)

    songs = db.relationship("Song", backref="SongType", lazy="dynamic")

    def __repr__(self):
        return f"<SongType {self.name}>"


# Die Sprache wird als ISO 639-1 Code gespeichert, z. B. "de" für Deutsch oder "en" für Englisch
class Language(db.Model):
    __tablename__ = "languages"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(2), index=True, unique=True, nullable=False)

    songs = db.relationship(
        "Song", secondary=song_language, back_populates="languages", lazy="dynamic"
    )

    def __repr__(self):
        return f"<Language {self.name}>"


class Genre(db.Model):
    __tablename__ = "genres"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), index=True, unique=True, nullable=False)

    songs = db.relationship(
        "Song", secondary=song_genre, back_populates="genres", lazy="dynamic"
    )

    def __repr__(self):
        return f"<Genre {self.name}>"


class Feel(db.Model):
    __tablename__ = "feels"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), index=True, unique=True, nullable=False)

    songs = db.relationship(
        "Song", secondary=song_feel, back_populates="feels", lazy="dynamic"
    )

    def __repr__(self):
        return f"<Feel {self.name}>"


class Speed(db.Model):
    __tablename__ = "speeds"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), index=True, unique=True, nullable=False)

    songs = db.relationship(
        "Song", secondary=song_speed, back_populates="speeds", lazy="dynamic"
    )

    def __repr__(self):
        return f"<Speed {self.name}>"


class Folder(db.Model):
    __tablename__ = "folders"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), index=True, unique=True, nullable=False)

    songs = db.relationship(
        "Song", secondary=song_folder, back_populates="folders", lazy="dynamic"
    )

    def __repr__(self):
        return f"<Folder {self.name}>"


class Series(db.Model):
    __tablename__ = "series"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), index=True, unique=True, nullable=False)

    songs = db.relationship(
        "Song", secondary=song_series, back_populates="series", lazy="dynamic"
    )

    def __repr__(self):
        return f"<Series {self.name}>"


class Tag(db.Model):
    __tablename__ = "tags"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), index=True, unique=True, nullable=False)

    songs = db.relationship(
        "Song", secondary=song_tag, back_populates="tags", lazy="dynamic"
    )

    def __repr__(self):
        return f"<Tag {self.name}>"
