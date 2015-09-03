import parsers.nginxParser
import tornado.ioloop
import tornado.web
import tornado.websocket
import queue
import pika

eventqueue = queue.Queue()


class ShadowParser(tornado.websocket.WebSocketHandler):
    def open(self, *args):
        print('ShadowParser websocket opened')
        print('ShadowBuster IP: ' + self.request.remote_ip)
        connection = pika.BlockingConnection()
        channel = connection.channel()
        channel.basic_consume(followqueue)

    def on_message(self, message):
        print(message)

    def on_close(self):
        print('WebSocket closed')

    # allow for cross-origin request
    def check_origin(self, origin):
        return True

    def followqueue(self):
        line, logtype = eventqueue.get(block=True)
        self.parseandserve(line, logtype)
        eventqueue.task_done()
        self.followqueue()

    @tornado.web.asynchronous
    def parseandserve(self, line, logtype):
        event = 0
        if logtype == 'nginx':
            event = parsers.nginxParser.parse(line)
        if event:
            self.write_message(event)

if __name__ == '__main__':
    app = tornado.web.Application([
        (r'/', ShadowParser),
        (r'/events', EventQueueHandler)
    ])
    app.listen(7777)
    tornado.ioloop.IOLoop.instance().start()
