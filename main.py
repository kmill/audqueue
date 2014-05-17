import os.path

import mqueue
import audacious

import model

import tornado.web
import tornado.ioloop
from tornado.options import define, options

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
            (r"/ajax/([^/]+)", AjaxHandler)
        ]

        tornado.web.Application.__init__(self, handlers, **settings)

        self.db = model.Database("data.db")
        self.queue = mqueue.MQueue.get_queues()['AudaciousQueue']()

class MainHandler(tornado.web.RequestHandler) :
    def get(self) :
        self.redirect("/static/index.html")

class AjaxHandler(tornado.web.RequestHandler) :
    def post(self, function) :
        if function == "songs" :
            self.finish({"result" : self.application.db.get_songs()})
        elif function == "queue" :
            try :
                self.application.queue.queue(json.loads(self.get_argument("filenames")))
                self.finish({"result" : "ok"})
            except Exception as x :
                print x
                self.finish({"error" : "Could not queue."})
        else :
            self.finish({"error" : "No such function."})

if __name__ == "__main__" :
    tornado.options.options.parse_command_line()
    print "Starting..."
    application = Application()
    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
