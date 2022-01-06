import tornado.ioloop
import asyncio
import tornado.web
import tornado.websocket
import RPi.GPIO as GPIO
import json
import os
import time
import random
from threading import Thread
from tornado.platform.asyncio import AnyThreadEventLoopPolicy
import queue

asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())
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
    print("Loading Routines")
    r = {}
    for filename in os.listdir(routinesPath):
        if filename[0] == ".":
            continue
        newline = ""
        with open(routinesPath+"/"+filename) as f:
            for line in f.readlines():
                line = line.replace("w", " w ");
                line = line.replace("r", " r ");
                for c in line:
                    if c.isdigit() == True or c == " " or c == "w" or c == "-" or c == "r":
                        newline = newline+c
        if len(newline) < 1:
          continue
        r[filename.capitalize()] = {}
        r[filename.capitalize()]['routine'] = newline
        r[filename.capitalize()]['state'] = 0
    print("Loading Routines - finished")
    return r

class Worker(Thread):
  def __init__(self, q, *args, **kwargs):
    self.q = q
    super().__init__(*args, **kwargs)
  def run(self):
    while True:
      try:
        work = self.q.get()
      except queue.Empty:
        continue
      # we re-enqueue because it's expected to run in a loop, and because this is synchronous here
      # if the queue is reset before or after it gets here it shouldn't matter
      # but only of it is not allon or alloff because those are steady states and don't need to loop
      if work['routine'] != 'Allon' and work['routine'] != 'Alloff':
        q.put_nowait(work)
      # then we run the routine
      work['web'].runRoutine(work['routine'])
      time.sleep(.5)
      self.q.task_done()

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")
class includeJsHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("include.js")
class reconnectingwebsocketHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("reconnecting-websocket.min.js")
 
class SimpleWebSocket(tornado.websocket.WebSocketHandler):
    connections = set()
    def initialize(self, q, routines):
        print(q)
        print(routines)
        self.q = q
        self.routines = routines

    def sendMessage(self, message):
        for client in self.connections:
            client.write_message(message)

    def setState(self, id, state):
        state = int(state)
        id = int(id)
        if state == 1:
            GPIO.output(pinmap[id], GPIO.HIGH)
        if state == 0:
            GPIO.output(pinmap[id], GPIO.LOW)
        pins[pinmap[id]][state] = GPIO.input(pin)
        message = {'action': 'state', 'id': id, 'state': state}
        self.sendMessage(message)

    def runRoutine(self,name):
        print("Running: "+name)
        routine = self.routines[name]['routine']
        tokens = routine.split()
        for t in tokens:
            if t == "w":
                time.sleep(.5)
                continue
            if t == "r":
                t = random.randrange(-8,8)
            t = int(t)
            if t == 0:
                for i in range(1,9):
                    self.setState(i,0)
                continue
            # negative numbers turn off, positive turn on
            toset = 1
            if t < 0:
                toset = 0
            t = abs(t)
            self.setState(t,toset)
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
        self.sendRoutines()

    def sendRoutines(self):
        for r in self.routines:
            message = {'action': 'routine', 'name': r}
            [client.write_message(message) for client in self.connections]
 
    def on_message(self, message):
        print(message)
        msg = json.loads(message)
        if msg['action'] == "setid":
            self.setState(msg['id'], msg['state'])
        if msg['action'] == "routine":
            self.q.put_nowait({'routine':msg['routine'],'web':self})
        if msg['action'] == "stop":
            self.clear_queue(q)

    def clear_queue(self,q):
        while not self.q.empty():
            self.q.get()
    def on_close(self):
        self.connections.remove(self)
 
def make_app(q,routines):
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/include.js", includeJsHandler),
        (r"/reconnecting-websocket.min.js", reconnectingwebsocketHandler),
        (r"/websocket", SimpleWebSocket, dict(q=q,routines=routines))
    ])

def start_tornado(q, routines):
    app = make_app(q, routines)
    server = tornado.httpserver.HTTPServer(app)
    server.listen(8080)
    tornado.ioloop.IOLoop.instance().start()

q = queue.Queue()
Worker(q).start()

t = Thread(target=start_tornado, args=(q, loadRoutines()))
t.daemon = True
t.start()
t.join()

