# audacious.py
#
# Provides support for Audacious

import mqueue
import subprocess

class AudaciousQueue(mqueue.MQueue) :
    def __init__(self) :
        pass
    def _audtool(self, arguments) :
        args = ["audtool"] + arguments
        if subprocess.call(args) :
            raise Exception("audtool returned non-zero exit code")
    def queue(self, filenames) :
        for filename in filenames :
            self._audtool(["playlist-addurl", filename])
