# mqueue.py
#
# This is the interface for things which are able to queue music
# files for playback.

class MQueue(object) :
    """Music file queue interface. Must have a zero-argument
    constructor."""
    def queue(self, filenames) :
        raise NotImplemented

    @classmethod
    def get_queues(cls) :
        queues = {}
        for scls in list(cls.__subclasses__()) :
            queues[scls.__name__] = scls
        return queues
