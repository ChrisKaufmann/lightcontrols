import tornado.ioloop
import tornado.web
import tornado.websocket
import RPi.GPIO as GPIO
import json
import os
import time

GPIO.setmode(GPIO.BOARD)

routinesPath = "routines"

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
def loadRoutines():
    r = {}
    for filename in os.listdir(routinesPath):
        newline = ""
        with open(routinesPath+"/"+filename) as f:
            for line in f.readlines():
                for c in line:
                    if c.isdigit() == True or c == " " or c == "w" or c == "-":
                        newline = newline+c
        if len(newline) < 1:
          continue
        r[filename.capitalize()] = newline
    return r
routines = loadRoutines()

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

    def runRoutine(self,routine):
        print("Running: "+routine)
        routine = routine.replace("w", " w ")
        tokens = routine.split()
        for t in tokens:
            if t == "w":
                time.sleep(.5)
                continue
            t = int(t)
            if t == 0:
                for i in range(1,9):
                    self.setState(i,0)
                continue
            toset = 1
            if t < 0:
                toset = 0
            t = abs(t)
            self.setState(t,toset)
            print(t)
        return
 
    # on opening of a new browser session
    def open(self):
        self.connections.add(self)
        for pin in pins:
            pins[pin]['state'] = GPIO.input(pin)
            returnlabel = 1
            if pins[pin]['state'] == GPIO.LOW:
                returnlabel = 0
            message = {'action': 'state', 'id': pins[pin]['name'], 'state': returnlabel}
            [client.write_message(message) for client in self.connections]
        for r in routines:
            message = {'action': 'routine', 'name': r, 'routine': routines[r]}
            [client.write_message(message) for client in self.connections]
 
    def on_message(self, message):
        print(message)
        msg = json.loads(message)
        if msg['action'] == "setid":
            self.setState(msg['id'], msg['state'])
        if msg['action'] == "routine":
            self.runRoutine(msg['routine'])
 
    def on_close(self):
        self.connections.remove(self)
 
def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/websocket", SimpleWebSocket)
    ])
 
if __name__ == "__main__":
    app = make_app()
    app.listen(80)
    tornado.ioloop.IOLoop.current().start()
