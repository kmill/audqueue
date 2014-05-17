import sqlite3
import os.path

class Database(object) :
    song_params = ['name', 'grouping', 'composer', 'artist', 'album', 'genre',
                   'tracknum', 'numbertracks', 'discnum', 'numberdiscs', 'filetype',
                   'filesize', 'bitrate', 'time', 'filename', 'modified']
    def __init__(self, dbfile) :
        if not os.path.isfile(dbfile) :
            raise TypeError("The database file must be created first.")
        self.DB = sqlite3.connect(dbfile, detect_types=sqlite3.PARSE_DECLTYPES)
        self.DB.row_factory = sqlite3.Row
    def get_song(self, filename) :
        for row in self.DB.execute("select * from song where filename=?", (filename,)) :
            return dict(row)
        return None
    def get_songs(self) :
        songs = []
        for row in self.DB.execute("select * from song") :
            songs.append(dict(row))
        return songs
    def insert_song(self, song) :
        self.DB.execute("insert into song (" + ','.join(self.song_params) + ") values (" + ','.join('?' for p in self.song_params) + ")",
                        tuple(song[p] for p in self.song_params))
    def update_song(self, song) :
        self.DB.execute("update song set " + ' and '.join(p + '=?' for p in self.song_params) + " where filename=?",
                        tuple(song[p] for p in self.song_params) + tuple(song['filename']))
    def __enter__(self) :
        self.DB.__enter__()
        return self
    def __exit__(self, type, value, tb) :
        self.DB.__exit__(type, value, tb)
