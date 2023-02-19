from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtGui import QPen, QColor, QBrush, QTransform
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsEllipseItem
from PyQt5.QtCore import QEvent, Qt, pyqtSlot, pyqtSignal, QVariant

from backend.board_manager import BoardManager, GameStage
from backend.game_piece import GamePiece

import numpy as np
import os

class MainWindow(QtWidgets.QMainWindow):

	# ************************************* INIT METHODS ******************************************
	def __init__(self) -> None:
		super().__init__()

		self.boardManager = BoardManager()
		self.gamePieces = {}

		self.load_ui()
		self.connect_all()

		self.initGraphics()

	def load_ui(self):
		cwd = os.getcwd()
		filename = os.path.splitext(os.path.basename(__file__))[0]
		uic.loadUi(cwd + "/ui_files/" + filename + ".ui", self)

	# Connects all the signals and slots
	def connect_all(self):
		# Connect UI elements
		self.gameBtn.clicked.connect(self.gameBtn_Clicked)

		# Connect signals from the board manager
		self.boardManager.gameStarted.connect(self.initGraphics)
		self.boardManager.gameEnded.connect(self.boardManager_GameEnded)

		self.boardManager.placePieceEvaluated.connect(self.placePiece_Evaluated)
		self.boardManager.removePieceEvaluated.connect(self.removePiece_Evaluated)
		self.boardManager.movePieceEvaluated.connect(self.movePiece_Evaluated)



	# ************************* INIT METHODS FOR THE GAME BOARD ***************
	# Draws the initial state of the board
	def initGraphics(self):
		# Radius of drawn circles
		self.RADIUS = 15

		# Width of the pen used to draw the board
		self.PEN_WIDTH = 5

		# Space between each space on the board grid
		self.GRID_SPACING = 70

		# Array containing the color of each player's pieces
		self.playerColors = np.empty(2, QColor)

		# Common colors used for drawing the board
		self.COLOR_BLACK = QColor(0, 0, 0)
		self.COLOR_RED = QColor(100, 0, 0)
		self.COLOR_BLUE = QColor(0, 0, 100)

		# ************** TESTING ONLY
		# TODO: find a better way of setting player colors
		# Set the color of player 1's pieces to red
		self.playerColors[0] = self.COLOR_RED
		# Set the color of player 2's pieces to blue
		self.playerColors[1] = self.COLOR_BLUE

		# Generate a new QGraphicsScene of the board
		self.drawBoard(self.boardManager.adjacentPieces)

		print("Initialized the graphics")

	# Generates a new QGraphicsScene based on the current state of the board
	def drawBoard(self, adjacentPieces):
		# Create a new empty scene
		scene = QGraphicsScene()

		# Create pen and brush for drawing board
		pen = QPen(self.COLOR_BLACK, self.PEN_WIDTH)
		brush = QBrush(QColor(100, 86, 30))

		# Add all the lines connecting the corners/intersections
		for rootPiece, connectedPieces in adjacentPieces.items():
			x1 = rootPiece[0]
			y1 = rootPiece[1]

			for piece in connectedPieces:
				x2 = piece[0]
				y2 = piece[1]

				scene.addLine(x1 * self.GRID_SPACING, y1 * self.GRID_SPACING, 
								x2 * self.GRID_SPACING, y2 * self.GRID_SPACING, pen)

		# Get the indices of all the corners and intersections
		indices = np.where(self.boardManager.boardState != None)

		# Change color for outline of corners/intersections
		pen.setColor(QColor(150, 126, 45))

		# Add all the corners/intersections to the scene
		for i in range(len(indices[0])):
			x = indices[0][i] * self.GRID_SPACING
			y = indices[1][i] * self.GRID_SPACING
			scene.addEllipse(x - self.RADIUS, y - self.RADIUS,
								self.RADIUS * 2, self.RADIUS * 2, 
								pen, brush)

		self.scene = scene

		# Show the scene in the graphics view
		self.graphicsView.setScene(scene)
		self.graphicsView.installEventFilter(self)


	# ****************************** UI EVENTS *************************************************
	# Event filter for the QGraphicsScene displaying the game board
	# Responsible for alerting the board manager of a piece placement or removal
	def eventFilter(self, obj: 'QObject', event: 'QEvent') -> bool:
		# Check if it is a mouse press event
		# Removes or places a piece depending on the current game stage
		if event.type() == QEvent.MouseButtonPress:
			pos = self.graphicsView.mapToScene(event.pos())
			# Convert to board coordinates
			x, y = self.sceneToBoard(pos.x(), pos.y())


			if self.boardManager.gameState == GameStage.PLACEMENT:
				# Send the piece placement move to the board
				self.boardManager.placePiece(x, y)

			elif self.boardManager.gameState == GameStage.REMOVAL or \
					self.boardManager.gameState == GameStage.FIRST_REMOVAL:
				# Get the game piece at the board coordinates
				piece = self.scene.itemAt(pos.x(), pos.y(), self.graphicsView.transform())

				if not isinstance(piece, GamePiece):
					print("Please click on a game piece")

				else:
					# Send the piece removal request to the board manager
					self.boardManager.removePiece(piece.ID)
				
			return True
			
		return super().eventFilter(obj, event)

	# Signal received from the game pieces
	# Responsible for alerting the board manager of any piece movement
	@pyqtSlot(int, float, float)
	def gamePiece_Moved(self, ID, x, y):
		# Convert to board coordinates for the board manager
		x, y = self.sceneToBoard(x, y)

		self.boardManager.movePiece(ID, x, y)

	# Responsible for alerting the board manager of the user wanting to start or end a game
	@pyqtSlot()
	def gameBtn_Clicked(self):
		# Tries to start a game
		if(not self.boardManager.gameRunning and self.boardManager.startGame()):
			self.gameBtn.setText("Forfeit")
			self.drawBoard(self.boardManager.adjacentPieces)

		# Tries to end the game
		elif(self.boardManager.gameRunning):
			self.boardManager.endGame()
			self.gameBtn.setText("New Game")


	# **************************** GAME EVENTS *************************************
	# Updates the board visuals after the board manager evaluates the piece placement request
	@pyqtSlot(bool, int, float, float, str, int)
	def placePiece_Evaluated(self, approved, ID, x, y, nextStage, nextPlayer):
		# ***RESPONDS TO THE OUTCOME OF THE PREVIOUS MOVE
		# Check if the piece placement has been approved
		if not approved:
			print("The piece couldn't be placed")
			return

		# Get the properties of the new game piece
		x, y = self.boardToScene(x, y)
		player = ID & (2**self.boardManager.ID_SHIFT - 1)

		# Create a new game piece
		newPiece = GamePiece(ID, x, y, self.RADIUS, self.playerColors[player])

		# Add the piece to the scene
		self.scene.addItem(newPiece)
		# Store the piece for future use
		self.gamePieces[ID] = newPiece

		# Connect the signals from the game piece
		newPiece.pieceMoved.connect(self.gamePiece_Moved)

		# ***PREPARES FOR THE NEXT MOVE
		# Update any UI elements
		self.gameStateLbl.setText("Player " + str(nextPlayer + 1) + "'s Turn")
		
		if (nextStage == "placement"):
			self.announcementLbl.setText("Click on spot to place a piece")
		elif (nextStage == "removal"):
			self.announcementLbl.setText("Click on a piece to remove")


	# Updates the board visuals after the board manager evaluates the piece removal request
	@pyqtSlot(bool, int, str, int, list)
	def removePiece_Evaluated(self, approved, ID, nextStage, nextPlayer, activePieces):
		# ***RESPONDS TO THE OUTCOME OF THE PREVIOUS MOVE
		if not approved:
			print("The piece couldn't be removed")
			return

		# Removes the game piece from the scene
		piece = self.gamePieces.pop(ID)
		self.scene.removeItem(piece)
		del piece

		print("The piece was successfully removed from the scene")

		# ***PREPARES FOR THE NEXT MOVE
		# Activates any pieces that can be moved in the next stage
		self.activatePlayer(activePieces)

		# Update any UI elements
		self.gameStateLbl.setText("Player " + str(nextPlayer + 1) + "'s Turn")
		
		if (nextStage == "movement"):
			self.announcementLbl.setText("Drag one of your pieces to an adjacent spot")

		elif (nextStage == "removal"):
			self.announcementLbl.setText("Click on a piece to remove")

		

	# Updates the board visuals after the board manager evaluates the piece movement request
	@pyqtSlot(bool, int, float, float, str, int, list)
	def movePiece_Evaluated(self, approved, ID, x, y, nextStage, nextPlayer, activePieces):
		# ***RESPONDS TO THE OUTCOME OF THE PREVIOUS MOVE
		# Get the piece corresponding to the evaluated piece movement
		piece = self.gamePieces[ID]

		# If piece movement was not approved, move the piece back to its original position
		if not approved:
			print("The piece couldn't be moved")
			piece.movePiece()
			return
		
		# Otherwise move it to its new position
		x, y = self.boardToScene(x, y)
		piece.movePiece(x, y)


		# ***PREPARES FOR THE NEXT MOVE
		# Activates any pieces that can be moved in the next stage
		self.activatePlayer(activePieces)

		# Update any UI elements
		self.gameStateLbl.setText("Player " + str(nextPlayer + 1) + "'s Turn")
		
		if (nextStage == "movement"):
			self.announcementLbl.setText("Drag one of your pieces to an adjacent spot")

		elif (nextStage == "removal"):
			self.announcementLbl.setText("Click on a piece to remove")

	# Updates the board visuals after the game ends
	@pyqtSlot()
	def boardManager_GameEnded(self):
		self.announcementLbl.setText("Game Over")
		self.gameBtn.setText("New Game")


	# **************************** BOARD-SCENE TRANSLATIONS **************************
	# Translates the scene's x and y coordinates to the nearest board index
	def sceneToBoard(self, x, y):
		board_x = round(x / self.GRID_SPACING)
		board_y = round(y / self.GRID_SPACING)
		
		return (board_x, board_y)

	# Translates the board's index to scene coordinates
	def boardToScene(self, x, y):
		scene_x = x * self.GRID_SPACING
		scene_y = y * self.GRID_SPACING

		return (scene_x, scene_y)

	# ************************** PIECE ACTIVATION METHODS ****************************
	# Activates the movable game pieces of the current player
	# while deactivating the pieces of all the other players
	@pyqtSlot(int)
	def activatePlayer(self, activePieces):
		for id, piece in self.gamePieces.items():
			if id in activePieces:
				piece.activate()
			else:
				piece.deactivate()
