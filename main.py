import os.path

import mqueue
import audacious
import remote_audacious
import minirpc

import model

import tornado.web
import tornado.ioloop
from tornado.options import define, options
from tornado.escape import url_escape, url_unescape

import json

define("port", default=3322, help="run on the given port", type=int)

class Application(tornado.web.Application) :
    def __init__(self) :
        settings = dict(
            app_title="Audqueue",
            template_path="templates",
            static_path="static",
        )

        handlers = [
            (r"/", MainHandler),
            (r"/ajax/([^/]+)", AjaxHandler),
            (r"/file/(.*)", FileHandler, {'path' : '/'})
        ]

        tornado.web.Application.__init__(self, handlers, **settings)

        self.destinations = []
        with open("config/destinations.json") as destsf :
            dests = json.load(destsf)
            for dest in dests :
                q = mqueue.MQueue.get_queues()[dest['type']](**dest['config'])
                self.destinations.append((dest['name'], q))

        self.db = model.Database("data.db")

class MainHandler(tornado.web.RequestHandler) :
    def get(self) :
        self.redirect("/static/index.html")

class AjaxHandler(tornado.web.RequestHandler) :
    def post(self, function) :
        if function == "songs" :
            self.finish({"result" : self.application.db.get_songs()})
        elif function == "destinations" :
            self.finish({"result" : [(dest[0], dest[1].url()) for dest in self.application.destinations]})
        elif function == "add" :
            try :
                for dest in self.application.destinations :
                    if dest[0] == self.get_argument("destination") :
                        dest[1].add(json.loads(self.get_argument("filenames")))
                        break
                self.finish({"result" : "ok"})
            except Exception as x :
                print x
                self.finish({"error" : "Could not queue."})
        elif function == "rpc" :
            def getMessage() :
                return json.loads(self.get_argument("message"))
            for dest in self.application.destinations :
                if isinstance(dest[1], audacious.AudaciousQueue) :
                    res = minirpc.handle_request(dest[1], getMessage)
                    self.finish({"result" : res})
                    return
            self.finish({"error" : "No local audacious queue"})
        else :
            self.finish({"error" : "No such function."})

class FileHandler(tornado.web.StaticFileHandler) :
    def parse_url_path(self, url_path) :
        url_path = os.path.abspath(os.path.join("/", url_unescape(url_path)))
        song = self.application.db.get_song(url_path)
        if not song :
            raise tornado.web.HTTPError(404)
        return song['filename']
    
    # def head(self, filename) :
    #     self.get(filename, include_body=False)
    # def get(self, filename, include_body=True) :
    #     song = self.application.db.get_song(filename)
    #     if not song :
    #         raise tornado.web.HTTPError(404)
    #     self.set_header("Content-Type", song['filetype'])
    #     shortfilename = "blah"
    #     self.set_header("Content-Disposition", "inline; filename=\"" + url_escape(shortfilename) + "\"")
    #     self.set_header("Content-Length", song['filesize'])
    #     mod = datetime.datetime.utcfromtimestamp(os.path.getmtime(song['filename']))
    #     self.set_header("Last-Modified", mod)
    #     ims_value = self.request.headers.get("If-Modified-Since")
    #     if ims_value is not None :
    #         date_tuple = email.utls.parsedate(ims_value)
    #         if_since = datetime.datetime.fromtimestamp(time.mktime(date_tuple))
    #         if if_since >= created :
    #             self.set_status(304)
    #             return
    #     if not include_body :
    #         return
    #     with open(song['filename'], "rb") as f:
    #         self.write(f.read())
    #     #self.flush()
    #     return
            
if __name__ == "__main__" :
    tornado.options.options.parse_command_line()
    print "Starting..."
    application = Application()
    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
