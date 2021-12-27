import tornado.ioloop
import tornado.web
import tornado.websocket
import RPi.GPIO as GPIO
import json

GPIO.setmode(GPIO.BOARD)

#directory of the pins
pins= {
   31 : {'name' : '3', 'state' : GPIO.LOW, 'keypress': 51},
   32 : {'name' : '6', 'state' : GPIO.LOW, 'keypress': 54},
   33 : {'name' : '4', 'state' : GPIO.LOW, 'keypress': 52},
   35 : {'name' : '1', 'state' : GPIO.LOW, 'keypress': 49},
   36 : {'name' : '5', 'state' : GPIO.LOW, 'keypress': 53},
   37 : {'name' : '2', 'state' : GPIO.LOW, 'keypress': 50},
   38 : {'name' : '7', 'state' : GPIO.LOW, 'keypress': 55},
   40 : {'name' : '8', 'state' : GPIO.LOW, 'keypress': 56}
  }
pinmap = {
  1: 35,
  2: 37,
  3: 31,
  4: 33,
  5: 36,
  6: 32,
  7: 38,
  8: 40
}

for pin in pins:
   GPIO.setup(pin, GPIO.OUT)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")
 
class SimpleWebSocket(tornado.websocket.WebSocketHandler):
    connections = set()

    def setState(self, id, state):
        state = int(state)
        id = int(id)
        if state == 1:
            GPIO.output(pinmap[id], GPIO.HIGH)
        if state == 0:
            GPIO.output(pinmap[id], GPIO.LOW)
        pins[pinmap[id]][state] = GPIO.input(pin)
        message = {'action': 'state', 'id': id, 'state': state}
        print(message)
        [client.write_message(message) for client in self.connections]
 
    # on opening of a new browser session
    def open(self):
        self.connections.add(self)
        for pin in pins:
            pins[pin]['state'] = GPIO.input(pin)
            returnlabel = 1
            if pins[pin]['state'] == GPIO.LOW:
                returnlabel = 0
            message = {'action':'state', 'id': pins[pin]['name'], 'state': returnlabel}
            [client.write_message(message) for client in self.connections]
 
    def on_message(self, message):
        print(message)
        msg = json.loads(message)
        if msg['action'] == "setid":
            self.setState(msg['id'], msg['state'])
        [client.write_message(message) for client in self.connections]
 
    def on_close(self):
        self.connections.remove(self)
 
def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/websocket", SimpleWebSocket)
    ])
 
if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
