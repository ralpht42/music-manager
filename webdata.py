import musicbrainzngs


class musicbrainz:
    def __init__(self):
        musicbrainzngs.set_useragent(
            "Special Music Manager", "0.1", "musicmanager@rberry.de"
        )

    def search_artist(self, artist):
        result = musicbrainzngs.search_artists(artist)
        return result

    def search_release(self, artist, release):
        result = musicbrainzngs.search_releases(artist=artist, release=release)
        return result

    def search_recording(self, artist, recording):
        result = musicbrainzngs.search_recordings(artist=artist, recording=recording)
        return result


if __name__ == "__main__":
    musicbrainz_instance = musicbrainz()
    artist = musicbrainz_instance.search_artist("The Beatles")
    print(artist)
    release = musicbrainz_instance.search_release("The Beatles", "Abbey Road")
    print(release)
    recording = musicbrainz_instance.search_recording("The Beatles", "Come Together")
    print(recording)
