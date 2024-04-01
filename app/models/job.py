from datetime import datetime, time
import pandas as pd

from app.extensions import db
from app.models.song import (
    song_artist_role,
    song_language,
    song_genre,
    song_feel,
    song_speed,
    song_folder,
    song_series,
    song_tag,
)
from app.models.song import (
    Song,
    SongType,
    Artist,
    Language,
    Genre,
    Feel,
    Speed,
    Folder,
    Series,
    Role,
    Tag,
)


song_job = db.Table(
    "song_job",
    db.Column("song_id", db.Integer, db.ForeignKey("songs.id"), primary_key=True),
    db.Column("job_id", db.Integer, db.ForeignKey("jobs.id"), primary_key=True),
)


class Job(db.Model):
    __tablename__ = "jobs"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), index=True, nullable=False)
    created_at = db.Column(
        db.DateTime, index=True, nullable=False, default=datetime.now()
    )
    updated_at = db.Column(
        db.DateTime, index=True, nullable=False, default=datetime.now()
    )
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_by_user = db.relationship('User', foreign_keys=[created_by])
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    updated_by_user = db.relationship('User', foreign_keys=[updated_by])
    manual = db.Column(db.Boolean, default=False, nullable=False)

    songs = db.relationship("Song", secondary=song_job, backref="Job", lazy="dynamic")

    def __repr__(self):
        return f"<Job {self.name}>"

    def __init__(self, name, created_by, manual=False):
        self.name = name
        self.created_by = created_by
        self.updated_by = created_by
        self.manual = manual
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def import_excel_file(self, file):
        df = None
        try:
            df = pd.read_excel(file)
        except Exception as e:
            raise Exception("Excel-Datei konnte nicht gelesen werden: " + str(e))

        for index, row in df.iterrows():
            # Überprüfung, ob die Zeilen mit den richtigen Datentypen gefüllt sind.
            # Falls nicht, wird die Zeile übersprungen.
            if (
                not row["Title"]
                or type(row["Title"]) != str
                or not row["Artists"]
                or type(row["Artists"]) != str
                or not row["Year"]
                or type(row["Year"]) not in [int, float]
                or not row["Language"]
                or type(row["Language"]) != str
                or not row["Length"]
                or type(row["Length"]) != time
                or not row["Genre"]
                or type(row["Genre"]) != str
                or not row["Type"]
                or type(row["Type"]) != str
            ):

                print("Zeile " + str(index) + " wird übersprungen.")
                continue

            # Erstellen des Typs, falls er noch nicht existiert.
            if not SongType.query.filter_by(name=row["Type"]).first():
                song_type = SongType(name=row["Type"])
                db.session.add(song_type)
                db.session.commit()

            seconds = row["Length"].second + row["Length"].minute * 60

            song = Song(
                title=row["Title"].strip(),
                duration=seconds,
                release_year=row["Year"],
                type_id=SongType.query.filter_by(name=row["Type"]).first().id,
                voice_percent=row["Voice %"],
                rap_percent=row["Rap % from Voice"],
                popularity_percent=row["Popularity %"],
                weird_percent=row["Weird %"],
            )
            db.session.add(song)
            db.session.commit()

            # Füge die Verknüpfung zwischen Song und Job hinzu.
            # Dadurch kann über den Job auf die Songs zugegriffen werden.
            job_song_entry = song_job.insert().values(
                song_id=song.id,
                job_id=self.id,
            )
            db.session.execute(job_song_entry)
            db.session.commit()

            """
            Erstellen der Verknüpfung zwischen dem Song, den Artists und den Rollen.
            """

            # Erstelle die Rolle, falls sie noch nicht existiert.
            roles = ["main", "featured"]
            for role in roles:
                if not Role.query.filter_by(name=role).first():
                    role = Role(name=role)
                    db.session.add(role)
                    db.session.commit()

            # Teile das Feld Artists in einzelne Interpreten auf.
            # Dabei wird zwischen Haupt- und Featured-Interpreten unterschieden.
            artists_in_roles = row["Artists"].split(" ft. ")

            artists = {
                "main": [artist.strip() for artist in artists_in_roles[0].split(", ")],
                "featured": (
                    [artist.strip() for artist in artists_in_roles[1].split(", ")]
                    if len(artists_in_roles) > 1
                    else []
                ),
            }

            for role in artists:
                for artist in artists[role]:
                    # Erstelle den Artist, falls er noch nicht existiert
                    if not Artist.query.filter_by(name=artist).first():
                        artist_object = Artist(name=artist)
                        db.session.add(artist_object)
                        db.session.commit()

                    # Erstelle die Verknüpfung zwischen Song, Rolle und Artist.
                    song_artist_role_entry = song_artist_role.insert().values(
                        song_id=song.id,
                        artist_id=Artist.query.filter_by(name=artist).first().id,
                        role_id=Role.query.filter_by(name=role).first().id,
                    )
                    db.session.execute(song_artist_role_entry)
                    db.session.commit()

            # TODO: Erstellen der Verknüpfung zwischen dem Song und den anderen Feldern.

            # Erstelle die Verknüpfung zwischen Song und Sprache.
            languages = row["Language"].split(", ")
            for language in languages:
                if not Language.query.filter_by(name=language).first():
                    language_object = Language(name=language)
                    db.session.add(language_object)
                    db.session.commit()

                song_language_entry = song_language.insert().values(
                    song_id=song.id,
                    language_id=Language.query.filter_by(name=language).first().id,
                )
                db.session.execute(song_language_entry)
                db.session.commit()

            # Erstelle die Verknüpfung zwischen Song und Genre.
            genres = row["Genre"].split(", ")
            for genre in genres:
                if not Genre.query.filter_by(name=genre).first():
                    genre_object = Genre(name=genre)
                    db.session.add(genre_object)
                    db.session.commit()

                song_genre_entry = song_genre.insert().values(
                    song_id=song.id,
                    genre_id=Genre.query.filter_by(name=genre).first().id,
                )
                db.session.execute(song_genre_entry)
                db.session.commit()

            # Erstelle die Verknüpfung zwischen Song und Feel.
            if row["Feels"] and type(row["Feels"]) == str:
                feels = row["Feels"].split(", ")
                for feel in feels:
                    if not Feel.query.filter_by(name=feel).first():
                        feel_object = Feel(name=feel)
                        db.session.add(feel_object)
                        db.session.commit()

                    song_feel_entry = song_feel.insert().values(
                        song_id=song.id,
                        feel_id=Feel.query.filter_by(name=feel).first().id,
                    )
                    db.session.execute(song_feel_entry)
                    db.session.commit()

            # Erstelle die Verknüpfung zwischen Song und Speed.
            if row["Speed"] and type(row["Speed"]) == str:
                speeds = row["Speed"].split(", ")
                for speed in speeds:
                    if not Speed.query.filter_by(name=speed).first():
                        speed_object = Speed(name=speed)
                        db.session.add(speed_object)
                        db.session.commit()

                    song_speed_entry = song_speed.insert().values(
                        song_id=song.id,
                        speed_id=Speed.query.filter_by(name=speed).first().id,
                    )
                    db.session.execute(song_speed_entry)
                    db.session.commit()

            # Erstelle die Verknüpfung zwischen Song und Folder.
            if row["Folder"] and type(row["Folder"]) == str:
                folders = row["Folder"].split(", ")
                for folder in folders:
                    if not Folder.query.filter_by(name=folder).first():
                        folder_object = Folder(name=folder)
                        db.session.add(folder_object)
                        db.session.commit()

                    song_folder_entry = song_folder.insert().values(
                        song_id=song.id,
                        folder_id=Folder.query.filter_by(name=folder).first().id,
                    )
                    db.session.execute(song_folder_entry)
                    db.session.commit()

            # Erstelle die Verknüpfung zwischen Song und Series.
            if row["Series"] and type(row["Series"]) == str:
                series = row["Series"].split(", ")
                for serie in series:
                    if not Series.query.filter_by(name=serie).first():
                        serie_object = Series(name=serie)
                        db.session.add(serie_object)
                        db.session.commit()

                    song_series_entry = song_series.insert().values(
                        song_id=song.id,
                        series_id=Series.query.filter_by(name=serie).first().id,
                    )
                    db.session.execute(song_series_entry)
                    db.session.commit()

            # Hinzufügen von Tags
            a = row["Legend"]
            if row["Legend"] and row["Legend"] == 1:
                if not Tag.query.filter_by(name="Legend").first():
                    tag_object = Tag(name="Legend")
                    db.session.add(tag_object)
                    db.session.commit()

                song_tag_entry = song_tag.insert().values(
                    song_id=song.id,
                    tag_id=Tag.query.filter_by(name="Legend").first().id,
                )
                db.session.execute(song_tag_entry)
                db.session.commit()

            """
            Platzhalter für weitere Tags
            """
