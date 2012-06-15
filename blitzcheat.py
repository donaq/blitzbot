from Xlib import X, display
from Xlib.X import ButtonPress, ButtonRelease
from Xlib.ext.xtest import fake_input
from SocketServer import TCPServer, StreamRequestHandler
from threading import Thread

class BlitzCheatHandler(StreamRequestHandler):
	def handle(self):
		req = self.request.recv(4096)
		print req
		self.request.sendall("""HTTP/1.0 200 OK\r\nContent-Type: text/html\r\nContent-Length: 1\r\n\r\n1\r\n\r\n""")
		req = req.split('\n')
		coords = [l.strip() for l in req if 'coords' in l][0]
		coords = [int(i) for i in coords.split("=")[1].split('+')]
		bc = BlitzCheater( coords[0], coords[1], coords[2], coords[3])
		bc.run()

class BlitzCheater(Thread):
	def __init__(self, x1, y1, x2, y2):
		super(BlitzCheater, self).__init__()
		self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2

		self.display = display.Display()
		self.root = self.display.screen().root
		self.stop = False

	def movepointer(self,x,y):
		self.root.warp_pointer(x,y)
		self.display.sync()

	def click(self):
		fake_input(self.display, ButtonPress, 1)
		self.display.sync()
		fake_input(self.display, ButtonRelease, 1)
		self.display.sync()

	def run(self):
		self.movepointer(self.x1+(self.x2-self.x1)/2+70, self.y1+(self.y2-self.y1)/2+70)
		self.click()
		self.movepointer(self.x1+(self.x2-self.x1)/2+110, self.y1+(self.y2-self.y1)/2+70)
		self.click()

	def kill(self):
		self.stop = True

if __name__=="__main__":
	server = TCPServer(('localhost',9999), BlitzCheatHandler)
	server.serve_forever()
