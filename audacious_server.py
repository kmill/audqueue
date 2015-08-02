# a server accepting connections to manipulate the audacious queue
# (and endpoint for RemoteAudacious)

import mqueue
import audacious
import minirpc

import tornado.web
import tornado.ioloop
from tornado.options import define, options

import json

define("port", default=3323, help="run on the given port", type=int)

class Application(tornado.web.Application) :
    def __init__(self) :
        settings = dict(app_title="Audacious playlist",
                        template_path="templates",
                        static_path="static")
        handlers = [
            (r"/", MainHandler),
            (r"/ajax/([^/]+)", AjaxHandler)
        ]

        tornado.web.Application.__init__(self, handlers, **settings)
        self.queue = mqueue.MQueue.get_queues()['AudaciousQueue']()

class MainHandler(tornado.web.RequestHandler) :
    def get(self) :
        self.redirect("/static/audacious_index.html")

class AjaxHandler(tornado.web.RequestHandler) :
    def post(self, function) :
        if function == "rpc" :
            def getMessage() :
                return json.loads(self.get_argument("message"))
            res = minirpc.handle_request(self.application.queue, getMessage)
            self.finish({"result" : res})
        else :
            self.finish({"error" : "No such function"})

if __name__ == "__main__" :
    tornado.options.options.parse_command_line()
    print "Starting..."
    application = Application()
    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
