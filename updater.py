import mutagen
import os
import os.path

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
                artist = "*Unknown Artist*"

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
