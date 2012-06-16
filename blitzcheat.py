from Xlib import X, display
from Xlib.X import ButtonPress, ButtonRelease
from Xlib.ext.xtest import fake_input
from SocketServer import TCPServer, StreamRequestHandler
from threading import Thread
from PIL import Image
import cv, gtk.gdk, time, math

def screenshot():
	"""Saves a screenshot"""
	w = gtk.gdk.get_default_root_window()
	sz = w.get_size()
	pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,False,8,sz[0],sz[1])
	pb = pb.get_from_drawable(w,w.get_colormap(),0,0,0,0,sz[0],sz[1])
	if (pb != None):
		pb.save("screenshot.png","png")
		print "Screenshot saved to screenshot.png."
	else:
		print "Unable to get the screenshot."

class BlitzCheatHandler(StreamRequestHandler):
	def handle(self):
		req = self.request.recv(4096)
		print req
		self.request.sendall("""HTTP/1.0 200 OK\r\nContent-Type: text/html\r\nContent-Length: 1\r\n\r\n1\r\n\r\n""")
		if 'coords' in req:
			req = req.split('\n')
			coords = [l.strip() for l in req if 'coords' in l][0]
			coords = [int(i) for i in coords.split("=")[1].split('+')]
			self.x1, self.y1, self.x2, self.y2 = coords[0], coords[1], coords[2], coords[3]
			self.calibrate()
			bc = BlitzCheater(self.x1, self.y1, self.x2, self.y2)
			bc.run()

	def calibrate(self, showgrid=True):
		screenshot()
		x1,y1,x2,y2 = self.x1,self.y1,self.x2,self.y2
		imcolor = cv.LoadImage('screenshot.png')
		image = cv.LoadImage('screenshot.png',cv.CV_LOAD_IMAGE_GRAYSCALE)

		edges = cv.CreateImage(cv.GetSize(image),8,1)
		cv.NamedWindow('Harris', cv.CV_WINDOW_AUTOSIZE)

		def getmean(image, x, y, w, h):
			cv.SetImageROI(image,(x,y,w,h))
			mean = cv.Avg(image)
			cv.ResetImageROI(image)
			return mean

		def getlines(image, edges, mean, orient, lim1, lim2, fun):
			cv.Canny(image,edges,0.65*mean[0],1.34*mean[0])
			lines = cv.HoughLines2(edges,cv.CreateMemStorage(),cv.CV_HOUGH_PROBABILISTIC,1,math.pi/2,3,30,4)
			return fun([line[0][orient] for line in lines if line[0][orient]==line[1][orient] and line[0][orient]>=lim1 and line[0][orient]<=lim2])

		# get left side
		mean = getmean(image, x1-5,y1,10,y2-y1)
		self.x1 = getlines(image, edges, mean, 0, x1-3, x1+3, max)

		# get right side
		mean = getmean(image, x2-5,y1,10,y2-y1)
		self.x2 = getlines(image, edges, mean, 0, x2-3, x2+3, max)+1

		# get top
		mean = getmean(image, x1, y1-5, x2-x1, 10)
		self.y1 = getlines(image, edges, mean, 1, y1-3, y1+3, min)

		# get bottom
		mean = getmean(image, x1, y2-5, x2-x1, 10)
		self.y2 = getlines(image, edges, mean, 1, y2-3, y2+3, max)

		if showgrid:
			self.showgrid(imcolor)

	def showgrid(self, imcolor):
		x1,y1,x2,y2 = self.x1,self.y1,self.x2,self.y2
		jumpx, jumpy = (x2-x1)/8, (y2-y1)/8
		
		for i in range(8):
			currx, curry = x1 + jumpx*i, y1 + jumpy*i
			cv.Line(imcolor, (x1, curry), (x2, curry), (0,0,255), 1)
			cv.Line(imcolor, (currx, y1), (currx, y2), (0,0,255), 1)
		
		cv.Line(imcolor, (x2,y1), (x2,y2), (0,0,255), 1)
		
		cv.NamedWindow('Harris', cv.CV_WINDOW_AUTOSIZE)
		cv.ShowImage('Harris', imcolor) # show the image
		cv.WaitKey()

class BlitzCheater(Thread):
	timelimit = 75 # number of seconds to play
	def __init__(self, x1, y1, x2, y2):
		super(BlitzCheater, self).__init__()
		self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
		self.width, self.height = (x2-x1)/8, (y2-y1)/8
		self.xmid, self.ymid = self.width/2, self.height/2

		self.display = display.Display()
		self.root = self.display.screen().root
		self.stop = False

	def movepointer(self,x,y):
		"""Moves pointer to x, y"""
		self.root.warp_pointer(x,y)
		self.display.sync()

	def click(self):
		"""Makes the mouse click"""
		fake_input(self.display, ButtonPress, 1)
		self.display.sync()
		fake_input(self.display, ButtonRelease, 1)
		self.display.sync()

	def makeboard(self):
		tiles = range(8)
		for j in tiles:
			for i in tiles:
				xmid, ymid= self.x1+i*self.width+self.xmid,self.y1+j*self.height+self.ymid
				self.movepointer(xmid, ymid)
				time.sleep(1)
				print self.screen[xmid,ymid],
			print ''

	def run(self):
		screenshot()
		self.movepointer(self.x1+(self.x2-self.x1)/2+70, self.y1+(self.y2-self.y1)/2+70)
		self.click()
		self.movepointer(self.x1+(self.x2-self.x1)/2+110, self.y1+(self.y2-self.y1)/2+70)
		self.click()

	# to signal stop playing
	def kill(self):
		self.stop = True

if __name__=="__main__":
	server = TCPServer(('localhost',9999), BlitzCheatHandler)
	server.serve_forever()
