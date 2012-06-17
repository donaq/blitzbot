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

def make_adjacency():
	"""Creates possible moves and positions to check for each position"""
	erange = range(8)
	matrix = [[None for i in erange] for j in erange]
	mvs = [{'mv':(0,-1)},{'mv':(0,1)},{'mv':(-1,0)},{'mv':(1,0)}]
	pls = lambda x,y:x+y
	movefun = lambda x,y: map(pls, x, y)
	for mv in mvs:
		# index to mutate for checks on positions perpendicular to movement
		m = mv['mv']
		perindex = 0 if m[1] else 1
		# index to mutate for checks on positions parallel to movement
		parindex = 0 if perindex else 1
		# get the transformation matrices for 2 more squares in the same direction
		parfactor = m[parindex]*1
		parchecks = ([0,0], [0,0])
		for i in (1,0):
			parchecks[i][parindex] += parfactor*(i+1)
		mv['checks'] = [parchecks]
		# get the tranformation matrices for squares perpendicular to target square
		for chks in ((-1,1), (-2,-1), (2,1)):
			perchecks = ([0,0], [0,0])
			for i,j in zip((0,1), chks):
				perchecks[i][perindex] += j
			mv['checks'].append(perchecks)

	for j in erange:
		for i in erange:
			moves = []
			# move up down left right
			for mv in mvs:
				checks = []
				to = movefun((i,j), mv['mv'])
				if -1 in to or 8 in to:
					continue
				mov = {'move':to}
				for check in mv['checks']:
					invalid = False
					chksquares = []
					for square in check:
						toto = movefun(to, square)
						if -1 in toto or 8 in toto:
							invalid = True
							break
						chksquares.append(toto)
					if invalid:
						continue
					checks.append(chksquares)
				mov['checks'] = checks
				moves.append(mov)
			matrix[i][j] = moves
	return matrix


class BlitzCheatHandler(StreamRequestHandler):
	def handle(self):
		req = self.request.recv(4096)
		print req
		self.request.sendall("""HTTP/1.0 200 OK\r\nContent-Type: text/html\r\nContent-Length: 1\r\n\r\n1\r\n\r\n""")
		try:
			print self.x1, self.y1, self.x2, self.y2
		except: pass
		if 'coords' in req:
			req = req.split('\n')
			coords = [l.strip() for l in req if 'coords' in l][0]
			coords = [int(i) for i in coords.split("=")[1].split('+')]
			self.x1, self.y1, self.x2, self.y2 = coords[0], coords[1], coords[2], coords[3]
			self.calibrate()
		elif 'playgame' in req:
			server = self.server
			bc = BlitzCheater(server.x1, server.y1, server.x2, server.y2)
			bc.run()
		elif "adjust" in req:
			server = self.server
			req = req.split('\n')
			adjustments = [l.strip() for l in req if 'adjust' in l][0]
			adjustments = [int(i) for i in adjustments.split("=")[1].split('+')]
			try:
				print "before:", server.x1, server.y1, server.x2, server.y2
				server.x1, server.y1, server.x2, server.y2 = map(lambda x,y: x+y, (server.x1, server.y1, server.x2, server.y2), adjustments)
				print "after:", server.x1, server.y1, server.x2, server.y2
				self.savegrid()
			except:
				print "Grid not initialized."

	def calibrate(self, showgrid=True):
		screenshot()
		server = self.server
		x1,y1,x2,y2 = self.x1,self.y1,self.x2,self.y2
		image = cv.LoadImage('screenshot.png',cv.CV_LOAD_IMAGE_GRAYSCALE)

		edges = cv.CreateImage(cv.GetSize(image),8,1)

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
		server.x1 = getlines(image, edges, mean, 0, x1-3, x1+3, max)

		# get right side
		mean = getmean(image, x2-5,y1,10,y2-y1)
		server.x2 = getlines(image, edges, mean, 0, x2-3, x2+3, max)+1

		# get top
		mean = getmean(image, x1, y1-5, x2-x1, 10)
		server.y1 = getlines(image, edges, mean, 1, y1-3, y1+3, min)

		# get bottom
		mean = getmean(image, x1, y2-5, x2-x1, 10)
		server.y2 = getlines(image, edges, mean, 1, y2-3, y2+3, max)

		self.savegrid()

	def savegrid(self):
		imcolor = cv.LoadImage('screenshot.png')
		x1,y1,x2,y2 = server.x1,server.y1,server.x2,server.y2
		jumpx, jumpy = (x2-x1)/8, (y2-y1)/8
		
		for i in range(8):
			currx, curry = x1 + jumpx*i, y1 + jumpy*i
			cv.Line(imcolor, (x1, curry), (x2, curry), (0,0,255), 1)
			cv.Line(imcolor, (currx, y1), (currx, y2), (0,0,255), 1)
		
		cv.Line(imcolor, (x2,y1), (x2,y2), (0,0,255), 1)
		cv.Line(imcolor, (x1,y2), (x2,y2), (255,0,255), 1)
		cv.SaveImage('grid.png', imcolor)
		

class BlitzCheater(Thread):
	timelimit = 75 # number of seconds to play
	def __init__(self, x1, y1, x2, y2):
		super(BlitzCheater, self).__init__()
		self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
		self.width, self.height = (x2-x1)/8, (y2-y1)/8
		self.xmid, self.ymid = self.width/2, self.height/2
		self.makeboard()

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
		self.board = [[(self.x1+i*self.width+self.xmid,self.y1+j*self.height+self.ymid) for i in tiles] for j in tiles]
	
	def movegem(self, fr, to):
		(i,j),(k,l) = fr, to
		self.movepointer(*self.board[i][j])
		self.click()
		self.movepointer(*self.board[k][l])
		self.click()

	def screenshot(self):
		screenshot()
		self.screen = Image.open("screenshot.png").load()

	def getmoves(self):
		rrange = range(7,-1,-1)
		moves = []
		for i in rrange:
			for j in rrange:
				to = self.getmovefrompos(i,j)
				if to: moves.append(((i,j), to))
		return moves

	def getmovefrompos(self, i, j):
		x,y = self.board[i][j]
		color = self.screen[x,y]
		maxmatch, maxindex = 0, 0
		for move,index in zip(matrix[i][j], range(len(matrix[i][j]))):
			to = move['move']
			matches = 0
			for check in move['checks']:
				for k,l in check:
					x,y = self.board[k][l]
					if color != self.screen[x,y]:
						break
				else:
					matches+=1
			if matches>maxmatch:
				maxmatch, maxindex = matches, index
		if maxmatch>0:
			return matrix[i][j][maxindex]['move']
		return None

	def run(self):
		runlimit = time.time()+self.timelimit
		while time.time()<runlimit:
			self.screenshot()
			moves = self.getmoves()
			for fr, to in moves:
				self.movegem(fr, to)
			time.sleep(0.3)


if __name__=="__main__":
	matrix = make_adjacency()
	server = TCPServer(('localhost',9999), BlitzCheatHandler)
	server.serve_forever()
