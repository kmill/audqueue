# mqueue.py
#
# This is the interface for things which are able to queue music
# files for playback.

class MQueue(object) :
    """Music file queue interface. Must have a zero-argument
    constructor."""
    def url(self) :
        raise NotImplemented
    def add(self, filenames) :
        raise NotImplemented
    def remove(self, pos) :
        raise NotImplemented
    def advance(self) :
        raise NotImplemented
    def reverse(self) :
        raise NotImplemented
    def queue(self, pos) :
        raise NotImplemented
    def dequeue(self, pos) :
        raise NotImplemented
    def jump(self, pos) :
        raise NotImplemented
    def playpause(self) :
        raise NotImplemented
    def setvolume(self, v) :
        raise NotImplemented
    def playlist(self) :
        return NotImplemented
    def clear(self) :
        return NotImplemented

    @classmethod
    def get_queues(cls) :
        queues = {}
        for scls in list(cls.__subclasses__()) :
            queues[scls.__name__] = scls
        return queues
