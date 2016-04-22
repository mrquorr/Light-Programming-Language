
from graphics import *

class Color(object):
	def __init__(self, r, g, b):
		self.r = r
		self.g = g
		self.b = b

class Hide(object):
	begin = -1
	end = -1
	active = False

class Show(object):
	begin = -1
	end = -1
	active = False

class Move(object):
	begin = -1
	end = -1
	x = -1
	y = -1
	active = False

class Scale(object):
	begin = -1
	end = -1
	size = -1
	active = False

class Vertex(object):
	def __init__(self, x, y):
		self.x = x
		self.y = y


class Figure(object):
	def __init__(self):
		self.hide = Hide()
		self.show = Show()
		self.move = Move()
		self.color = Color(0,0,0)

	def setColor(self, r, g, b):
		self.color.r = r
		self.color.g = g
		self.color.b = b

	def getColor(self):
		return color_rgb(self.color.r, self.color.g, self.color.b)

class L_Circle(Figure):
	def __init__(self, x, y, radius):
		super(self.__class__, self).__init__()
		self.radius = radius
		self.center = Vertex(x, y)

	def getPointCenter(self):
		return Point(self.center.x, self.center.y)

class L_Triangle(Figure):
	def __init__(self):
		super(self.__class__, self).__init__()
		self.vertices = [Vertex(0,0), Vertex(0,0), Vertex(0,0)]
	
	def setVertex(self, num, x, y):
		self.vertices[num].x = x
		self.vertices[num].y = y

	def getVertex(self, num):
		return (self.vertices[num].x, self.vertices[num].y)

	def getPointsList(self):
		l = []
		for vertex in self.vertices:
			l.append( Point(vertex.x, vertex.y) )
		return l

class L_Rectangle(Figure):
	def __init__(self, x1, y1, x2, y2):
		super(self.__class__, self).__init__()
		self.v1 = Vertex(x1, y1)
		self.v2 = Vertex(x2, y2)

	def getPoints(self):
		return (Point(self.v1.x, self.v1.y), Point(self.v2.x, self.v2.y))

class L_Point(Figure):
	def __init__(self, x, y):
		super(self.__class__, self).__init__()
		self.center = Vertex(x, y)

	def getPoint(self):
		return Point(self.center.x, self.center.y)

class L_Square(Figure):
	def __init__(self, x, y, size):
		super(self.__class__, self).__init__()
		self.size = size
		self.v1 = Vertex(x, y)
		self.v2 = Vertex(x+size, y+size)

	def getPoints(self):
		return (Point(self.v1.x, self.v1.y), Point(self.v2.x, self.v2.y))

class L_Polygon(Figure):
	def __init__(self, numVertices):
		super(self.__class__, self).__init__()
		self.vertices = []
		self.numVertices = numVertices

	def setVertex(self, num, x, y):
		self.vertices[num].x = x
		self.vertices[num].y = y

	def getVertex(self, num):
		return (self.vertices[num].x, self.vertices[num].y)

	def getPointsList(self):
		l = []
		for vertex in self.vertices:
			l.append( Point(vertex.x, vertex.y) )
		return l

	def addVertex(self, x, y):
		self.vertices.append(Vertex(x,y))


##NO STAR #@$% that!