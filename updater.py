import mutagen
import os
import os.path
import xml.parsers.expat as expat
import dateutil.parser
from datetime import datetime, timedelta
import calendar
import urllib
import unicodedata

def totimestamp(dt) :
    return calendar.timegm(dt.utctimetuple())

def do_directory_sync(db, directory) :
    with db :
        for root, dirs, files in os.walk(unicode(directory)) :
            for filename in files :
                update_file(db, directory, root, filename)

def update_file(db, directory, root, filename) :
    full_filename = os.path.join(root, filename)
    modified = os.path.getmtime(full_filename)
    
    song = db.get_song(full_filename)
    if song == None or song['modified'] < modified :
        info = None
        try :
            info = mutagen.File(full_filename, easy=True)
        except :
            pass
        if info != None :
            name = info.get("title", [filename])[0]
            grouping = info.get("grouping", [None])[0]
            composer = info.get("composer", [None])[0]
            artist = info.get("artist", [None])[0]
            albumname = info.get("album", [None])[0]
            try :
                genre = info.get("genre", [None])[0]
            except :
                genre = None
            time = int(info.info.length*1000) # sec -> msec
            tracknum = info.get("tracknumber", [None])[0]
            numbertracks = None
            if tracknum != None and len(tracknum.split("/")) > 1 :
                tracknum, numbertracks = tracknum.split("/")
            # try to get the tracknum from the beginning of the track
            # name if the tracknum is None
            if tracknum == None :
                i = 1
                while i < len(name) :
                    try :
                        tracknum = int(name[:i])
                        i += 1
                    except ValueError :
                        break
            if tracknum != None :
                try :
                    tracknum = int(tracknum)
                except ValueError :
                    tracknum = None
                    numbertracks = None
            if numbertracks != None :
                try :
                    numbertracks = int(numbertracks)
                except ValueError :
                    numbertracks = None
            discnum = info.get("discnumber", [None])[0]
            numberdiscs = None
            if discnum == None :
                dirparts = os.path.split(root)
                if dirparts[1].lower().startswith("cd") and len(dirparts[1]) > 2 and dirparts[1][2:3] in "0123456789" :
                    discnum = dirparts[1][2:]
                    # this is the actual root of the album:
                    root = dirparts[0]
            if discnum != None and len(discnum.split("/")) > 1 :
                discnum, numberdiscs = discnum.split("/")
            if discnum != None :
                try :
                    discnum = int(discnum)
                except ValueError :
                    discnum = None
                    numberdiscs = None
            if numberdiscs != None :
                try :
                    numberdiscs = int(numberdiscs)
                except ValueError :
                    numberdiscs = None
            filetype = info.mime[0]
            filesize = os.path.getsize(full_filename)
            try :
                bitrate = int(info.info.bitrate/1000) # bps -> kbps
            except AttributeError :
                bitrate = None # flac, for example

            if albumname == None :
                head, tail = os.path.split(root)
                if tail == "" or len(head) < len(directory) :
                    albumname = "*Unknown Album*"
                else :
                    albumname = tail
            if artist == None :
                artist = ""

            new_song = {
                'name' : name,
                'grouping' : grouping,
                'composer' : composer,
                'artist' : artist,
                'album' : albumname,
                'genre' : genre,
                'time' : time,
                'tracknum' : tracknum,
                'numbertracks' : numbertracks,
                'discnum' : discnum,
                'numberdiscs' : numberdiscs,
                'filetype' : filetype,
                'filesize' : filesize,
                'bitrate' : bitrate,
                'filename' : full_filename,
                'modified' : modified
            }
            if song == None :
                db.insert_song(new_song)
            else :
                db.update_song(new_song)
            print "processed", full_filename
        else :
            print "... ignoring", full_filename

class DoneException(Exception) :
    def __str__(self) :
        return "Done"

def do_itunes_sync(db, library_dir) :
    with db :
        xmlparser = expat.ParserCreate()
        isync = iTunesSyncer(xmlparser, db, library_dir)
        try :
            xmlparser.ParseFile(open(os.path.join(library_dir, "iTunes Music Library.xml"), 'r'))
        except DoneException :
            # we want to get here. We hit playlists
            pass

iTunesKindsDict = {"AAC audio file" : "audio/mp4",
                   "AIFF audio file" : "audio/x-aiff",
                   "Apple Lossless audio file" : "audio/mp4a",
                   "MPEG audio file" : "audio/mpeg",
                   "MPEG audio stream" : "audio/x-mpegurl",
                   "MPEG-4 video file" : "video/mp4",
                   "WAV audio file" : "audio/x-wav"}

iTunesSkipKinds = {"Protected AAC audio file" : True,
                   "QuickTime movie file" : True,
                   "Protected MPEG-4 video file" : True,
                   "Purchased AAC audio file" : True}

def iTunesKindToMime(kind) :
    return iTunesKindsDict[kind.strip()]

def skipiTunesKind(kind) :
    return iTunesSkipKinds.get(kind.strip(), False)

class iTunesSyncer(object) :
    def __init__(self, xmlparser, db, library_dir) :
        xmlparser.StartElementHandler = lambda name, attr : self.StartElementHandler(name, attr)
        xmlparser.EndElementHandler = lambda name : self.EndElementHandler(name)
        xmlparser.CharacterDataHandler = lambda data : self.CharacterDataHandler(data)
        self.currentdict = None
        self.currentkey = None
        self.currentmode = None
        self.do_data = False
        self.level = 0 # only start when level=2
        self.db = db
        self.library_dir = library_dir
        self.skippedSongs = []
    def StartElementHandler(self, name, attr) :
        if name == "dict" :
            if self.level < 2 :
                self.level += 1
            else :
                self.currentdict = {}
                self.level = 3
        elif name == "key" :
            if self.level == 3 :
                self.currentmode = "key"
                self.currentkey = ""
        elif name == "array" :
            raise DoneException
        elif self.currentmode == "data" :
            self.do_data = True
    def CharacterDataHandler(self, data) :
        if self.level == 3 :
            if self.currentmode == "key" :
                self.currentkey += data
            elif self.currentmode == "data" :
                if self.currentkey == u'Playlist Items' :
                    raise DoneException
                if self.do_data :
                    self.currentdict[self.currentkey] += data
    def EndElementHandler(self, name) :
        if self.level == 2 :
            if name == "array" :
                raise DoneException
        if self.level == 3 :
            if name == "key" :
                self.currentmode = "data"
                self.currentdict[self.currentkey] = ''
            elif self.do_data == True :
                self.do_data = False
            elif name == "dict" :
                self.level = 2
                if not self.currentdict.has_key("Album") :
                    self.currentdict["Album"] = "*Unknown Album*"
                if not self.currentdict.has_key("Artist") :
                    self.currentdict["Artist"] = ""
                
                d = self.currentdict

                loc2 = urllib.unquote(d['Location'])
                
                try :
                    loc2 = unicodedata.normalize('NFC', loc2.encode('iso-8859-1').decode('utf8'))
                except :
                    print repr(loc2)
                    pass

                try :
                    location = os.path.join(self.library_dir, loc2.split("iTunes/", 1)[1])
                except :
                    print "... could not process location", d['Location']
                    return
                if not os.path.isfile(location) :
                    print "... could not locate", location
                    return
                song = db.get_song(location)

                try :
                    modified = dateutil.parser.parse(d.get("Date Modified", None))
                except :
                    modified = None

                def nint(x) :
                    if x == None :
                        return None
                    else :
                        return int(x)

                if (not skipiTunesKind(d["Kind"])) and (modified is not None) :
                    new_song = {
                        'name' : d.get("Name", None),
                        'grouping' : d.get("Grouping", None),
                        'composer' : d.get("Composer", None),
                        'artist' : d.get("Artist", None),
                        'album' : d.get("Album", None),
                        'genre' : d.get("Genre", None),
                        'time' : nint(d.get("Total Time", None)),
                        'tracknum' : nint(d.get("Track Number", None)),
                        'numbertracks' : nint(d.get("Track Count", None)),
                        'discnum' : nint(d.get("Disc Number", None)),
                        'numberdiscs' : nint(d.get("Disc Count", None)),
                        'filetype' : iTunesKindToMime(d['Kind']),
                        'filesize' : nint(d.get("Size", None)),
                        'bitrate' : nint(d.get("Bit Rate", None)),
                        'filename' : location,
                        'modified' : totimestamp(modified)
                    }
                    if False :
                        print new_song
                        raw_input()
                    if song == None :
                        db.insert_song(new_song)
                    else :
                        db.update_song(new_song)
                    print "processed", location
                else :
                    print "... ignoring", location


def doInferGroupings(db) :
    print "Inferring groupings..."
    with db :
        albums = []
        for row in db.DB.execute("select album, COUNT(*) from song group by album") :
            albums.append(row['album'])
        for album in albums :
            noGroupings = True
            songnames = []
            for row in db.DB.execute("select filename, name, grouping, tracknum from song where album=?", (album,)) :
                if row['grouping'] :
                    noGroupings = False
                    break
                songnames.append((row['filename'], row['name'], row['tracknum']))
            if noGroupings :
                print "Album", album, "has no groupings"
                new_groupings = make_grouping(songnames)
                if False :
                    print new_groupings
                    raw_input()
                if new_groupings :
                    print "... inferred groupings"
                for filename, grouping in new_groupings.iteritems() :
                    song = db.get_song(filename)
                    song['grouping'] = grouping
                    db.update_song(song)
    print "done inferring groupings"

MIN_NUMBER_FOR_GROUPING = 3
MIN_GROUPING_NAME_LENGTH = 8

def make_grouping(songnames) :
    def getprefix(s1, s2) :
        maxlen = min(len(s1), len(s2))
        last_with_delimiter = 0
        for i in xrange(1, maxlen) :
            if s1[:i] != s2[:i] :
                return s1[:last_with_delimiter]
            if s1[i-1] in ":-," : # include space?
                last_with_delimiter = i-1
        else :
            return ""
        return s1[:maxlen]
    prefixes = {}
    for song_id, name, tracknum in songnames : # use tracknum?
        for prefix in prefixes.keys() :
            p = getprefix(name, prefix)
            prefixes.setdefault(p, set()).add(song_id)
            prefixes[p].update(prefixes[prefix])
        prefixes.setdefault(name, set()).add(song_id)
    prefixes2 = {}
    for prefix, ids in prefixes.iteritems() :
        cleaned_prefix = prefix.split(':')[0]
        while len(cleaned_prefix) > 0 :
            if cleaned_prefix[-1] in "IVX " :
                cleaned_prefix = cleaned_prefix[:-1]
            elif cleaned_prefix[-1] in ':-' :
                cleaned_prefix = cleaned_prefix[:-1].rstrip()
                break
            else :
                break
        prefixes2.setdefault(cleaned_prefix, set()).update(ids)
    prefixes = prefixes2
    just_prefixes = []
    for prefix, ids in prefixes.iteritems() :
        if len(ids) >= MIN_NUMBER_FOR_GROUPING :
            just_prefixes.append(prefix)
    def length_based_sort(x, y) :
        s = cmp(len(x), len(y))
        if s == 0 :
            return cmp(x, y)
        else :
            return s
    just_prefixes.sort(cmp=length_based_sort)
    groupings = {}
    for p in reversed(just_prefixes) :
        if any(i in groupings for i in prefixes[p]) :
            continue
        if len(p) < MIN_GROUPING_NAME_LENGTH :
            break
        for i in prefixes[p] :
            groupings[i] = p
    return groupings
                

if __name__ == "__main__" :
    import model
    db = model.Database("data.db")
    if True :
        with open("config/sources.txt", "r") as fin :
            for line in fin :
                line = line.strip().split("=",1)
                if line :
                    if line[0] == "directory" :
                        print "* directory", line[1]
                        do_directory_sync(db, line[1])
                    elif line[0] == "itunes" :
                        print "* itunes", line[1]
                        do_itunes_sync(db, line[1])
                    else :
                        raise Exception("unknown source type: " + line[0])
    if True :
        doInferGroupings(db)
    print "done."
                    
