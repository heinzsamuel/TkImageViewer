from tkinter import *
from tkinter import filedialog, Menu
from PIL import ImageTk, Image
from time import sleep
from random import random
from threading import Timer
from math import floor
import json

import os

FNAME_CONFIG = 'conf'
SUPPORTED_FILETYPES = [
	'bmp',
	'gif',
	'jpeg',
	'jpg',
	'ico',
	'png',
	'sgi',
	'tga',
	'tiff',
	'webp'
]



class Config:
	def __init__(self):
		self.config = {}
		self.attributes = [
			['window_width', 1000],
			['window_height', 800],
			['autoscale', True]
		]
		for attr in self.attributes:
			self.define_attribute(attr[0])

		try:
			self.config = self.load()
			self.repairConfig()
		except FileNotFoundError:
			self.resetConfig()
			self.save()
		print('config: ', self.config)

	def define_attribute(self, attr):
		self.config[attr] = None
		def getter(recentInstance, self):
			return self.config[attr]
		exec('self.get_'+attr+' = getter.__get__(self, type(self))')

		def setter(recentInstance, self, val):
			print('setting '+attr+' to ', val)
			self.config[attr] = val
		exec('self.set_'+attr+' = setter.__get__(self, type(self))')

		exec(self.__class__.__name__+'.'+attr + ' = property(self.get_'+attr+', self.set_'+attr+')')

	def repairConfig(self):
		for attr in self.attributes:
			if attr[0] not in self.config:	
				print('Adding missing key', attr[0])
				self.config[attr[0]] = attr[1]
		attributes = map(lambda attr: attr[0], self.attributes)
		for attr in self.config:
			attributes = map(lambda attr: attr[0], self.attributes)
			if attr not in attributes:
				print('Unexpected additional key ', attr)

	def resetConfig(self):
		for attr in self.attributes:
			self.config[attr[0]] = attr[1]

	def save(self):
		print('saving config: ', self.config)
		with open(FNAME_CONFIG, 'w') as outfile:
			json.dump(self.config, outfile)	

	def load(self):
		with open(FNAME_CONFIG) as json_file:
			config = json.load(json_file)
		return config

	# def get_lastOpenedFile(self):
	# 	return self.config['last_opened_file']
	
	# def set_lastOpenedFile(self, val):
	# 	self.config['last_opened_file'] = val

	# last_opened_file = property(get_lastOpenedFile, set_lastOpenedFile)

class ImageHandler:
	def __init__(self):
		self.current_file = None
		self.current_directory = None
		self.filenames = []
		self.images = []

	def loadImage(self, filename):
		self.current_file = filename
		self.loadFilenames()
		self.stripNonImageFileNames()

	def loadFilenames(self):
		self.current_directory = os.path.dirname(os.path.realpath(self.current_file))
		(_, _, self.filenames) = next(os.walk(self.current_directory))

	def stripNonImageFileNames(self):
		self.filenames = list(filter(lambda filename: filename.split('.')[-1].lower() in SUPPORTED_FILETYPES, self.filenames))

	def getFilename(self):
		return self.current_file.split('/')[-1].split('\\')[-1]

	def getCurrentIndex(self):
		try:
			current_index = self.filenames.index(self.getFilename())
		except ValueError:
			current_index = 0
		return current_index

	def getOffsetFilename(self, offset):
		current_index = self.getCurrentIndex()
		offset_index = (current_index + offset) % len(self.filenames)
		print('current image index = ', current_index)
		print('offset image index = ', offset_index)
		return self.filenames[offset_index]

	def getLeftFilename(self):
		return self.current_directory + '\\' + self.getOffsetFilename(-1)

	def getRightFilename(self):
		return self.current_directory + '\\' + self.getOffsetFilename(1)

# class EventService:
# 	def __init__(self, window):
# 		self.window = window

class ImageViewer:
	def __init__(self, window):
		self.window = window
		self.config = Config()
		self.image_handler = ImageHandler()
		self.configureWindow()
		
		#self.myContainer1 = Frame(window)
		#self.myContainer1.pack()

		self.image = None
		self.refreshScreenTimer = None

		self.label = Label(self.window, image = self.image)
		self.label.pack(side = "bottom", fill = "both", expand = "yes")

		self.label.bind('<Double-Button-1>', self.toggleAutoscale)

		self.window.bind('<Button-1>', self.leftButtonPressEvent)
		self.window.bind('<ButtonRelease-1>', self.leftButtonReleaseEvent)
		self.window.bind('<Motion>', self.mouseMoveEvent)


		self.ignoreConfigure = False

		self.image_x = 0
		self.image_y = 0

		self.down_x = None
		self.down_y = None

		# if self.config.last_opened_file:
		# 	self.openLastOpenedImage()

		# self.window.mainloop()

	def toggleAutoscale(self, event):
		self.config.autoscale = not self.config.autoscale
		self.refreshWindow()

	def configureWindow(self):
		self.createMenu()

		self.window.config(background='grey')
		self.window.geometry(str(self.config.window_width)+'x'+str(self.config.window_height))
		self.window.title("Image Viewer")

		self.window.bind("<Configure>", self.configureEvent)
		self.window.bind("<Left>", self.leftKeyEvent)
		self.window.bind("<Right>", self.rightKeyEvent)
		self.window.bind("<Control-o>", self.promptToOpenImage)

		self.window.protocol("WM_DELETE_WINDOW", self.exit)

	def leftButtonPressEvent(self, event):
		# print('press at (',event.x,',',event.y,')')
		(mouse_x, mouse_y) = self.absoluteMouseCoordinates()
		self.down_x = mouse_x
		self.down_y = mouse_y

	def leftButtonReleaseEvent(self, event):
		(mouse_x, mouse_y) = self.absoluteMouseCoordinates()
		offset_x = mouse_x - self.down_x
		offset_y = mouse_y - self.down_y
		# print('release')
		# print('offset_x = ', offset_x)
		# print('offset_y = ', offset_y)
		self.image_x = self.image_x + offset_x
		self.image_y = self.image_y + offset_y

		self.down_x = None
		self.down_y = None

		self.refreshWindow()

	def mouseMoveEvent(self, event):
		if (not self.down_x):
			return

		(mouse_x, mouse_y) = self.absoluteMouseCoordinates()

		# print('down_x = ',self.down_x)
		offset_x = mouse_x - self.down_x
		offset_y = mouse_y - self.down_y
		# print('move')
		# print('offset_x = ', offset_x)
		# print('offset_y = ', offset_y)
		self.image_x = self.image_x + offset_x
		self.image_y = self.image_y + offset_y

		self.down_x = mouse_x
		self.down_y = mouse_y

		self.refreshWindow()

	def absoluteMouseCoordinates(self):
		x = self.window.winfo_pointerx() - self.window.winfo_rootx()
		y = self.window.winfo_pointery() - self.window.winfo_rooty()
		return (x, y)

	def exit(self):
		print('Exiting')
		self.config.save()
		self.window.destroy()

	def createMenu(self):
		self.menubar = Menu(self.window)
		self.filemenu = Menu(self.menubar, tearoff=0)
		self.filemenu.add_command(label="Open", command=self.promptToOpenImage)
		self.filemenu.add_separator()
		self.filemenu.add_command(label="Exit", command=self.window.quit)
		self.menubar.add_cascade(label="File", menu=self.filemenu)
		self.window.config(menu=self.menubar)

	def promptToOpenImage(self, event=None):
		# filetypes = (("jpeg files","*.jpg"),("all files","*.*"))
		filetypes = (('all files', '*.*'),) + tuple(map(lambda x: (x, "*." + x), SUPPORTED_FILETYPES))
		filename = filedialog.askopenfilename(initialdir = "/", title = "Select file", filetypes = filetypes)
		if len(filename) == 0:
			self.image = None
			return

		self.openImage(filename)

	# def openLastOpenedImage(self):
	# 	if self.config.last_opened_file:
	# 		self.openImage(self.config.last_opened_file)
	# 	else:
	# 		self.image = None

	def openImage(self, filename):
		print('opening', filename)
		self.image_handler.loadImage(filename)
		self.image = Image.open(filename)
		self.window.title(self.image_handler.getFilename())
		# self.config.last_opened_file = filename
		self.image_width, self.image_height = self.image.size
		self.image_old_width = 0
		self.image_old_height = 0
		self.image_ratio = self.image_width / self.image_height

		self.image_x = 0
		self.image_y = 0

		print('image width', self.image_width)
		print('image height', self.image_height)
		print('image ratio', self.image_ratio)

		self.refreshWindow()

	def printAutoscaledImage(self):
		window_width = self.window.winfo_width()
		window_height = self.window.winfo_height()
		window_ratio = window_width / window_height

		if window_ratio > self.image_ratio:
			# print('option 1 - ', int(window_height * self.image_ratio), window_height)
			self.printScaledImage(int(window_height * self.image_ratio), window_height)
		else:
			# print('option 2 - ', window_width, int(window_width / self.image_ratio))
			self.printScaledImage(window_width, int(window_width / self.image_ratio))

	def printScaledImage(self, width, height):
		if self.image == None:
			return

		if width == self.image_old_width and height == self.image_old_height:
			return

		resizedImage = self.image.resize((width, height), Image.ANTIALIAS)
		self.tkimage = ImageTk.PhotoImage(resizedImage)
		self.label.configure(image = self.tkimage)

		self.image_old_width = width
		self.image_old_height = height
		# self.ignoreConfigure = True
		# self.label.update_idletasks()
		# self.ignoreConfigure = False

	def openLeftFilename(self):
		filename = self.image_handler.getLeftFilename()
		self.openImage(filename)

	def openRightFilename(self):
		filename = self.image_handler.getRightFilename()
		self.openImage(filename)

	def configureEvent(self, event):
		if self.ignoreConfigure:
			return

		# event.width and event.height can randomly be the image width and height
		#  if the config event was triggered when autoscale is active. winfo is unaffected

		self.config.window_width = self.window.winfo_width()
		self.config.window_height = self.window.winfo_height()
		
		if self.refreshScreenTimer != None:
			self.refreshScreenTimer.cancel()
		self.refreshScreenTimer = Timer(0.1, self.refreshWindow)
		self.refreshScreenTimer.start()

	def leftKeyEvent(self, event):
		self.openLeftFilename()

	def rightKeyEvent(self, event):
		self.openRightFilename()

	def refreshWindow(self):
		if self.image == None:
			return

		if self.config.autoscale:
			self.printAutoscaledImage()
		else:
			image_x = floor(self.window.winfo_width() / 2) + self.image_x
			image_y = floor(self.window.winfo_height() / 2) + self.image_y
			print('printing image at ', image_x, ',', image_y)
			self.label.place(x = image_x, y = image_y, anchor = 'center') 
			self.printScaledImage(self.image_width, self.image_height)

		# self.ignoreConfigure = True
		# self.label.update_idletasks()
		# self.ignoreConfigure = False
		self.refreshScreenTimer = None

window = Tk()
app = ImageViewer(window)
window.mainloop()