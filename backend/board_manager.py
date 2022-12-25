from enum import Enum
import numpy as np

from PyQt5.QtWidgets import QGraphicsScene, QGraphicsEllipseItem
from PyQt5.QtGui import QPen, QColor, QBrush
from PyQt5 import Qt

from .game_piece import GamePiece
from backend import rule_manager

# Enum for tracking what stage the game is in
class GameStage(Enum):
	STOPPED = 0
	PLACEMENT = 1
	MOVEMENT = 2

class BoardManager():
	# Constructor function
	def __init__(self) -> None:
		# ************** SETTING VALUES ******************************
		# Total number of players
		self.TOTAL_PLAYERS = 2

		# Maximum number of pieces each player can have
		self.MAX_PIECES = 12

		# Radius of drawn circles
		self.RADIUS = 15

		# Width of the pen used to draw the board
		self.PEN_WIDTH = 5

		# Space between each space on the board grid
		self.GRID_SPACING = 70

		# How far of a piece can be from the center of its new location
		# Goes from 0 to 1
		self.MARGIN_OF_ERROR = .2


		# ***************** GAME VARIABLES **************************
		# Represents whose turn it is
		# 0 indexed so for example, a value of 0 means it's player 1's turn
		self.current_turn = 0

		# The total number of pieces that each player has
		self.total_pieces = 0

		# Array containing all the game pieces
		self.gamePieces = np.empty((self.TOTAL_PLAYERS, self.MAX_PIECES), GamePiece)

		# Array containing the color of each player's pieces
		self.playerColors = np.empty(self.TOTAL_PLAYERS, QColor)

		# *** TESTING ONLY
		# Set the color of player 1's pieces to red
		self.playerColors[0] = QColor(100, 0, 0)
		# Set the color of player 2's pieces to blue
		self.playerColors[1] = QColor(0, 0, 100)

		# ******************** BOARD VARIABLES *********************

		# Size of the board
		self.boardSize = 7

		# Represents the current state of the board
		# Any index with a value of 0 means that there is no piece there
		# Any index with a value of 1 means that player 1 has a piece there
		# Any index with a value of 2 means that player 2 has a piece there
		# Any index with a value of None means that a piece is not allowed
		# to be placed there (the index is neither on an intersection or corner)
		self.boardState = np.array([[    0,     None,   None,   0,      None,   None,   0    ],
									[   None,  0,      None,   0,      None,   0,      None ],
									[   None,  None,   0,      0,      0,      None,   None ],
									[   0,     0,      0,      None,   0,      0,      0    ],
									[   None,  None,   0,      0,      0,      None,   None ],
									[   None,  0,      None,   0,      None,   0,      None ],
									[   0,     None,   None,   0,      None,   None,   0    ]])


		# TODO: Look into potentially generating the connections automatically
		# 		from the board layout
		# Represents which corners/intersections are connected to each other
		self.CONNECTIONS = np.array([# Outer Square
								[[0, 0], [0, 3]],	[[0, 3], [0, 6]],
								[[0, 6], [3, 6]],	[[3, 6], [6, 6]],
								[[6, 6], [6, 3]],	[[6, 3], [6, 0]],
								[[6, 0], [3, 0]],	[[3, 0], [0, 0]],
								# Middle Square
								[[1, 1], [1, 3]],	[[1, 3], [1, 5]],
								[[1, 5], [3, 5]],	[[3, 5], [5, 5]],
								[[5, 5], [5, 3]],	[[5, 3], [5, 1]],
								[[5, 1], [3, 1]],	[[3, 1], [1, 1]],
								# Inner Square
								[[2, 2], [2, 3]],	[[2, 3], [2, 4]],
								[[2, 4], [3, 4]],	[[3, 4], [4, 4]],
								[[4, 4], [4, 3]],	[[4, 3], [4, 2]],
								[[4, 2], [3, 2]],	[[3, 2], [2, 2]],
								# Between Outer and Middle Square
								[[0, 0], [1, 1]],	[[0, 3], [1, 3]],
								[[0, 6], [1, 5]],	[[3, 6], [3, 5]],
								[[6, 6], [5, 5]],	[[6, 3], [5, 3]],
								[[6, 0], [5, 1]],	[[3, 0], [3, 1]],
								# Between Middle and Inner Square
								[[1, 1], [2, 2]],	[[1, 3], [2, 3]],
								[[1, 5], [2, 4]],	[[3, 5], [3, 4]],
								[[5, 5], [4, 4]],	[[5, 3], [4, 3]],
								[[5, 1], [4, 2]],	[[3, 1], [3, 2]]])
		
		# TODO: Come up with a better name for the 'MOVEMENT' game stage
		# GameStage = Enum('GameStage', ['STOPPED', 'PLACEMENT', 'MOVEMENT'])
		gameState = GameStage.STOPPED

	# Sets the board to all its initial values and starts the game
	def startGame(self):
		# Represents whose turn it is
		# 0 indexed so for example, a value of 0 means it's player 1's turn
		self.current_turn = 0

		# The total number of pieces that each player has
		self.total_pieces = 0

		# Array containing all of Player 1's pieces
		self.playerOnePieces = np.empty(self.MAX_PIECES, GamePiece)

		# Array containing all of Player 2's pieces
		self.playerTwoPieces = np.empty(self.MAX_PIECES, GamePiece)

		# Changes the game to the placement stage
		self.gameState = GameStage.PLACEMENT

	# Generates a new QGraphicsScene based on the current state of the board
	def drawBoard(self):
		# Create a new empty scene
		scene = QGraphicsScene()

		# Create pen and brush for drawing board
		pen = QPen(QColor(0, 0, 0), self.PEN_WIDTH)
		brush = QBrush(QColor(100, 86, 30))

		# Add all the lines connecting the corners/intersections
		for connection in self.CONNECTIONS:
			x1 = connection[0][0]
			y1 = connection[0][1]
			x2 = connection[1][0]
			y2 = connection[1][1]

			scene.addLine(x1 * self.GRID_SPACING, y1 * self.GRID_SPACING, 
							x2 * self.GRID_SPACING, y2 * self.GRID_SPACING, pen)


		# Get the indices of all the corners and intersections
		indices = np.where(self.boardState != None)

		# Change color for outline of corners/intersections
		pen.setColor(QColor(150, 126, 45))

		# Add all the corners/intersections to the scene
		for i in range(len(indices[0])):
			x = indices[0][i] * self.GRID_SPACING
			y = indices[1][i] * self.GRID_SPACING
			scene.addEllipse(x - self.RADIUS, y - self.RADIUS,
								self.RADIUS * 2, self.RADIUS * 2, 
								pen, brush)

		# # TESTING ONLY:
		# # Add piece to board
		# self.gamePieces[0][0] = GamePiece(x=0, y=0, radius=self.RADIUS, 
		# 									color=self.playerColors[0])
		# scene.addItem(self.gamePieces[0][0])

		self.scene = scene

		# Return the finished scene
		return scene


	# Takes in a game piece's x and y then returns the closest valid position for it to move to
	# Returns None if there is no nearby valid position
	# Returns new x and y values if the position is valid
	# Snaps to grid
	# TODO: rename this method to better describe it
	def getValidPosition(self, old_x, old_y, new_x, new_y):
		# Convert from scene to board coordinates
		old_board_x, old_board_y = self.sceneToBoard(old_x, old_y)
		target_x, target_y = self.sceneToBoard(new_x, new_y)

		# 
		if (self.isValidSpot(new_x, new_y) and
			rule_manager.isValidMove(old_board_x, old_board_y, 
										target_x, target_y, self.boardState)):
			return self.boardToScene(target_x, target_y)
			
		else:
			print("Not a valid position")
			return None

	# Checks if the board coordinates are on a corner/intersection or not
	def isValidSpot(self, scene_x, scene_y):
		true_x = scene_x/ self.GRID_SPACING
		true_y = scene_y / self.GRID_SPACING

		target_x = round(true_x)
		target_y = round(true_y)

		x_error = abs(target_x - true_x)
		y_error = abs(target_y - true_y)
		# print(x_error, y_error)

		# print(boardState[target_y][target_x])

		# Check if spot is near a valid corner/intersection on the board
		onValidSpot = x_error <= self.MARGIN_OF_ERROR and \
						y_error <= self.MARGIN_OF_ERROR and \
						target_x >= 0 and target_x < self.boardSize and \
						target_y >= 0 and target_y < self.boardSize and \
						self.boardState[target_y][target_x] == 0
						
		return onValidSpot

	# Places a new game piece on the board at the scene coordinates (x, y)
	def placePiece(self, x, y):
		# if gameState == GameStage.Placement:		
		if not self.isValidSpot(x, y):
			print("Please press on a valid spot")
			return

		print("Player " + str(self.current_turn + 1) + "'s turn. Piece " + str(self.total_pieces + 1))
		
		board_x, board_y = self.sceneToBoard(x, y)
		scene_x, scene_y = self.boardToScene(board_x, board_y)

		# Should be playerColors[current_turn]
		self.gamePieces[self.current_turn][self.total_pieces] = \
				GamePiece(scene_x, scene_y, self.RADIUS, self.playerColors[self.current_turn])
		
		# Adds the new game piece to the scene
		self.scene.addItem(self.gamePieces[self.current_turn][self.total_pieces])

		# Update the board's state
		self.boardState[board_y][board_x] = self.current_turn + 1

		# Go to the next player's turn
		self.current_turn += 1

		# If all player's put down a piece, 
		# restart the order and have them place another piece
		if self.current_turn >= self.TOTAL_PLAYERS:
			self.current_turn %= self.TOTAL_PLAYERS
			self.total_pieces += 1

		# If all the pieces have been placed,
		# go on to the second stage of the game
		if self.total_pieces >= self.MAX_PIECES:
			gameState = GameStage.MOVEMENT
			print("Going to the movement stage")

	# TODO: finish implementing
	def changeStage(nextStage):
		if(nextStage == GameStage.PLACEMENT):
			pass
		elif(nextStage == GameStage.MOVEMENT):
			pass

	# Translates the scene's x and y coordinates to the nearest board index
	def sceneToBoard(self, x, y):
		board_x = round(x / self.GRID_SPACING)
		board_y = round(y / self.GRID_SPACING)
		
		return [board_x, board_y]

	# Translates the board's indes to scene coordinates
	def boardToScene(self, x, y):
		scene_x = x * self.GRID_SPACING
		scene_y = y * self.GRID_SPACING

		return [scene_x, scene_y]