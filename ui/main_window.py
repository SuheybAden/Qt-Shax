from PyQt5 import QtWidgets, uic, QtGui, QtCore
from backend import board_manager
import os

class MainWindow(QtWidgets.QMainWindow):
	def __init__(self) -> None:
		super().__init__()
		self.load_ui()

	def load_ui(self):
		cwd = os.getcwd()
		filename = os.path.splitext(os.path.basename(__file__))[0]
		uic.loadUi(cwd + "/ui_files/" + filename + ".ui", self)
		self.initGraphics()
		self.connect_all()

	def initGraphics(self):
		# Initialize the state of the board
		board_manager.initBoard()

		# Generate a new QGraphicsScene of the board
		scene = board_manager.drawBoard()

		# Show the scene in the graphics view
		self.graphicsView.setScene(scene)

	# Connects all the signals and slots
	def connect_all(self):
		pass