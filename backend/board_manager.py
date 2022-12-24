from enum import Enum
import numpy as np

from PyQt5.QtWidgets import QGraphicsScene, QGraphicsEllipseItem
from PyQt5.QtGui import QPen, QColor, QBrush
from PyQt5 import Qt

from .game_piece import GamePiece
from backend import rule_manager

# Maximum number of pieces each player can have
MAX_PIECES = 12

# Radius of drawn circles
RADIUS = 15

# Width of the pen used to draw the board
PEN_WIDTH = 5

# Space between each space on the board grid
GRID_SPACING = 70

# How far of a piece can be from the center of its new location
# Goes from 0 to 1
MARGIN_OF_ERROR = .2

# The total number of pieces that each player has
total_pieces = 0

# Array containing all of Player 1's pieces
playerOnePieces = np.empty(MAX_PIECES, GamePiece)

# Array containing all of Player 2's pieces
playerTwoPieces = np.empty(MAX_PIECES, GamePiece)

# Represents which corners/intersections are connected to each other
CONNECTIONS = np.array([# Outer Square
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

# Represents the current state of the board
# Any index with a value of 0 means that there is no piece there
# Any index with a value of 1 means that player 1 has a piece there
# Any index with a value of 2 means that player 2 has a piece there
# Any index with a value of None means that a piece is not allowed
# to be placed there (the index is neither on an intersection or corner)
boardState = np.array([[    0,     None,   None,   0,      None,   None,   0    ],
						[   None,  0,      None,   0,      None,   0,      None ],
						[   None,  None,   0,      0,      0,      None,   None ],
						[   0,     0,      0,      None,   0,      0,      0    ],
						[   None,  None,   0,      0,      0,      None,   None ],
						[   None,  0,      None,   0,      None,   0,      None ],
						[   0,     None,   None,   0,      None,   None,   0    ]])


# Enum for tracking what stage the game is in
# class GameStage(Enum):
# 	STOPPED = 0
# 	PLACEMENT = 1
# 	MOVEMENT = 2

# TODO: Come up with a better name for the 'MOVEMENT' game stage
GameStage = Enum('GameStage', ['STOPPED', 'PLACEMENT', 'MOVEMENT'])
gameState = GameStage.STOPPED

# Initialize the game board
def initBoard():
	pass

# Generates a new QGraphicsScene based on the current state of the board
def drawBoard():
	# Create a new empty scene
	scene = QGraphicsScene()

	# Create pen and brush for drawing board
	pen = QPen(QColor(100, 86, 30), PEN_WIDTH)
	brush = QBrush(QColor(100, 86, 30))

	# Add all the lines connecting the corners/intersections
	for connection in CONNECTIONS:
		x1 = connection[0][0]
		y1 = connection[0][1]
		x2 = connection[1][0]
		y2 = connection[1][1]

		scene.addLine(x1 * GRID_SPACING, y1 * GRID_SPACING, 
						x2 * GRID_SPACING, y2 * GRID_SPACING, pen)


	# Get the indices of all the corners and intersections
	indices = np.where(boardState != None)

	# Change color for outline of corners/intersections
	pen.setColor(QColor(150, 126, 45))

	# Add all the corners/intersections to the scene
	for i in range(len(indices[0])):
		x = indices[0][i] * GRID_SPACING
		y = indices[1][i] * GRID_SPACING
		scene.addEllipse(x - RADIUS, y - RADIUS,
							RADIUS * 2, RADIUS * 2, 
							pen, brush)

	# # TESTING ONLY:
	# # Add piece to board
	# playerOnePieces[0] = GamePiece(x=0, y=0, radius=RADIUS)
	# scene.addItem(playerOnePieces[0])

	# Return the finished scene
	return scene


# Takes in a game piece's x and y then returns if it is a valid position on the board or not
# Returns None if the position is not valid
# Returns new x and y values if the position is valid
# Snaps to grid
def getValidPosition(old_x, old_y, new_x, new_y):
	old_true_x = round(old_x / GRID_SPACING)
	old_true_y = round(old_y / GRID_SPACING)

	true_x = new_x / GRID_SPACING
	true_y = new_y / GRID_SPACING

	target_x = round(true_x)
	target_y = round(true_y)

	if(abs(target_x - true_x) > MARGIN_OF_ERROR and 
		abs(target_y - true_y) > MARGIN_OF_ERROR and 
		isValidSpot(target_x, target_y) and
		not rule_manager.isValidMove(old_true_x, old_true_y, target_x, target_y, boardState)):
		print("Not a valid position")
		return None
		
	
	else:
		return [target_x * GRID_SPACING, target_y * GRID_SPACING]

def placePiece(x, y):
	board_coord = sceneToBoard(x, y)


def isValidSpot(board_x, board_y):
	return boardState[board_y][board_x] == 0

# Translates the scene's x and y coordinates to the nearest board index
def sceneToBoard(x, y):
	board_x = round(x / GRID_SPACING)
	board_y = round(y / GRID_SPACING)
	
	return [board_x, board_y]

# Translates the board's indes to scene coordinates
def boardToScene(x, y):
	scene_x = x * GRID_SPACING
	scene_y = y * GRID_SPACING

	return [scene_x, scene_y]

target_x, target_y = sceneToBoard(200, 300)