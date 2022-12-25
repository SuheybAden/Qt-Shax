from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtCore import QEvent, Qt
from backend.board_manager import BoardManager
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

	# Connects all the signals and slots
	def connect_all(self):
		self.gameBtn.clicked.connect(self.gameBtn_Clicked)
		
	def initGraphics(self):
		# # Initialize the state of the board
		# board_manager.initBoard()
		self.board_manager = BoardManager()

		# Generate a new QGraphicsScene of the board
		scene = self.board_manager.drawBoard()

		# Show the scene in the graphics view
		self.graphicsView.setScene(scene)
		self.graphicsView.installEventFilter(self)

	def eventFilter(self, obj: 'QObject', event: 'QEvent') -> bool:
		if event.type() == QEvent.MouseButtonPress:
			pos = self.graphicsView.mapToScene(event.pos())
			self.board_manager.placePiece(pos.x(), pos.y())
			return True
			
		return super().eventFilter(obj, event)



	def gameBtn_Clicked(self):
		print("Game button has been clicked")
		self.board_manager.startGame()