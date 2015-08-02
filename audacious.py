# audacious.py
#
# Provides support for Audacious

import mqueue
import subprocess
from minirpc import rpcmethod, RPCServable

class AudaciousQueue(RPCServable, mqueue.MQueue) :
    def __init__(self) :
        self.playlist = {}
        self.queue = []
        self.position = -1
        self.status = None
        self.volume = None
    def _audtool(self, handler, *arguments) :
        args = ["audtool", handler] + list(arguments)
        return subprocess.check_output(args)
    def _update(self) :
        self.playlist = {}
        self.queue = []
        try :
            self.position = int(self._audtool("playlist-position"))
        except :
            self.position = -1
        self.status = self._audtool("playback-status").strip()
        self.volume = int(self._audtool("get-volume").strip())
        songs = self._audtool("playlist-display").split("\n")
        for song in songs[1:-2] :
            snum, _ = song.split("|", 1)
            num = int(snum)
            self.playlist[num] = song
        queue = self._audtool("playqueue-display").split("\n")
        for q in queue[1:-2] :
            _, snum, _ = q.split("|", 2)
            self.queue.append(int(snum))
    def url(self) :
        return "http://localhost:3322/static/audacious_index.html"
    @rpcmethod
    def advance(self) :
        self._audtool("playlist-advance")
    @rpcmethod
    def reverse(self) :
        self._audtool("playlist-reverse")
    @rpcmethod
    def queue(self, pos) :
        self._audtool("playqueue-add", str(int(pos)))
    @rpcmethod
    def dequeue(self, pos) :
        self._audtool("playqueue-remove", str(int(pos)))
    @rpcmethod
    def jump(self, pos) :
        self._audtool("playlist-jump", str(int(pos)))
    @rpcmethod
    def remove(self, pos) :
        self._audtool("playlist-delete", str(int(pos)))
    @rpcmethod
    def add(self, uris) :
        for uri in uris :
            self._audtool("playlist-addurl", str(uri))
    @rpcmethod
    def playpause(self) :
        self._audtool("playback-playpause")
    @rpcmethod
    def setvolume(self, v) :
        """v is a percentage"""
        self._audtool("set-volume", str(int(v)))
    @rpcmethod
    def playlist(self) :
        self._update()
        return { 'playlist' : self.playlist,
                 'queue' : self.queue,
                 'position' : self.position,
                 'status' : self.status,
                 'volume' : self.volume }
    @rpcmethod
    def clear(self) :
        self._audtool("playlist-clear")
