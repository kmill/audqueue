import mqueue
import json
import tornado.httpclient
import urllib

class RemoteAudaciousQueue(mqueue.MQueue) :
    def __init__(self, fileprefix, host) :
        self.fileprefix = fileprefix
        self.host = host

    def _rpc(self, method, **kwargs) :
        args = {
            "message" : json.dumps({"method" : method, "kwargs" : kwargs})
        }
        tornado.httpclient.AsyncHTTPClient().fetch(
            "http://" + self.host + "/ajax/rpc",
            self._rpc_resp,
            method="POST",
            body=urllib.urlencode(args)
        )
    def _rpc_resp(self, response) :
        pass
    def _make_uri(self, uri) :
        from tornado.escape import url_escape
        uri = self.fileprefix + "/" + url_escape(uri)
        print "_make_uri", uri
        return uri
    def url(self) :
        return "http://" + self.host + "/static/audacious_index.html"
    def advance(self) :
        self._rpc("advance")
    def reverse(self) :
        self._rpc("reverse")
    def queue(self, pos) :
        self._rpc("queue")
    def dequeue(self, pos) :
        self._rpc("dequeue")
    def jump(self, pos) :
        self._rpc("jump")
    def remove(self, pos) :
        self._rpc("remove")
    def add(self, uris) :
        self._rpc("add", uris=[self._make_uri(uri) for uri in uris])
    def playpause(self) :
        self._rpc("playpause")
    def setvolume(self, v) :
        """v is a percentage"""
        self._rpc("setvolume", v=v)
    def playlist(self) :
        return None

