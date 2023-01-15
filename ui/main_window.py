from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtCore import QEvent, Qt, pyqtSlot, pyqtSignal
from backend.board_manager import BoardManager, GameStage
import os

class MainWindow(QtWidgets.QMainWindow):
	def __init__(self) -> None:
		super().__init__()

		self.boardManager = BoardManager()
		self.load_ui()
		self.initGraphics()
		self.connect_all()

	def load_ui(self):
		cwd = os.getcwd()
		filename = os.path.splitext(os.path.basename(__file__))[0]
		uic.loadUi(cwd + "/ui_files/" + filename + ".ui", self)



	# Connects all the signals and slots
	def connect_all(self):
		self.gameBtn.clicked.connect(self.gameBtn_Clicked)
		self.boardManager.newText.connect(self.boardManager_NewText)
		self.boardManager.gameEnded.connect(self.boardManager_GameEnded)
		
	def initGraphics(self):
		# # Initialize the state of the board
		# boardManager.initBoard()

		# Generate a new QGraphicsScene of the board
		scene = self.boardManager.drawBoard()

		# Show the scene in the graphics view
		self.graphicsView.setScene(scene)
		self.graphicsView.installEventFilter(self)

	def eventFilter(self, obj: 'QObject', event: 'QEvent') -> bool:
		if event.type() == QEvent.MouseButtonPress:
			pos = self.graphicsView.mapToScene(event.pos())
			if self.boardManager.gameState == GameStage.PLACEMENT:
				self.boardManager.placePiece(pos.x(), pos.y())
			elif self.boardManager.gameState == GameStage.REMOVAL:
				self.boardManager.removePiece(pos.x(), pos.y())
			return True
			
		return super().eventFilter(obj, event)

	@pyqtSlot()
	def gameBtn_Clicked(self):
		if(not self.boardManager.gameRunning and self.boardManager.startGame()):
			self.gameBtn.setText("Forfeit")
		elif(self.boardManager.gameRunning):
			self.boardManager.endGame()
			self.gameBtn.setText("New Game")

	@pyqtSlot(str)
	def boardManager_NewText(self, text):
		self.announcementLabel.setText(text)

	@pyqtSlot()
	def boardManager_GameEnded(self):
		self.announcementLabel.setText("Game Over")
		self.gameBtn.setText("New Game")