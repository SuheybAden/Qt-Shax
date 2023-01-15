from enum import Enum
import numpy as np

from PyQt5.QtWidgets import QGraphicsScene, QGraphicsEllipseItem
from PyQt5.QtGui import QPen, QColor, QBrush
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5 import Qt

from .game_piece import GamePiece

# Enum for tracking what stage the game is in
# TODO: Come up with a better name for the 'MOVEMENT' game stage
class GameStage(Enum):
	STOPPED = 0
	PLACEMENT = 1
	REMOVAL = 2
	MOVEMENT = 3

class BoardManager(QObject):
	# *************** SIGNALS
	newText = pyqtSignal(str)
	gameEnded = pyqtSignal()

	# Constructor function
	def __init__(self) -> None:
		super().__init__()

		# ************** SETTING VALUES ******************************
		# Total number of players
		self.TOTAL_PLAYERS = 2

		# Maximum number of pieces each player can have
		self.MAX_PIECES = 5

		# Radius of drawn circles
		self.RADIUS = 15

		# Width of the pen used to draw the board
		self.PEN_WIDTH = 5

		# Common colors used for drawing the board
		self.COLOR_BLACK = QColor(0, 0, 0)
		self.COLOR_RED = QColor(100, 0, 0)
		self.COLOR_BLUE = QColor(0, 0, 100)

		# Space between each space on the board grid
		self.GRID_SPACING = 70

		# How far of a piece can be from the center of its new location
		# Goes from 0 to 1
		self.MARGIN_OF_ERROR = .2


		# ***************** GAME VARIABLES **************************
		# Tracks if a game is currently running or not
		self.gameRunning = False

		# Represents whose turn it is
		# 0 indexed so for example, a value of 0 means it's player 1's turn
		self.current_turn = 0

		# The total number of pieces that each player has
		self.total_pieces = 0

		self.firstToJare = None

		self.firstRemoval = True

		# Array for keeping track of every players' game pieces
		self.gamePieces = np.empty(self.TOTAL_PLAYERS, GamePiece)
		for i in range(self.TOTAL_PLAYERS):
			self.gamePieces[i] = []

		# Array for keeping track of each players' remaining pieces
		self.remainingPieces = np.ones(self.TOTAL_PLAYERS, int) * self.MAX_PIECES

		# Array for tracking how many active pieces each player has
		self.activePieces = np.zeros(self.TOTAL_PLAYERS, np.int8)

		# Array containing the total number of "jare" each player has made
		self.currentJare = np.zeros(self.TOTAL_PLAYERS, np.int8)

		# List of all the pieces currently in a "jare"
		self.piecesInJare = []

		# Array containing the color of each player's pieces
		self.playerColors = np.empty(self.TOTAL_PLAYERS, QColor)

		# *** TESTING ONLY
		# Set the color of player 1's pieces to red
		self.playerColors[0] = self.COLOR_RED
		# Set the color of player 2's pieces to blue
		self.playerColors[1] = self.COLOR_BLUE

		# ******************** BOARD VARIABLES *********************

		# Size of the board
		self.boardSize = 7

		# Represents the current state of the board
		# Any index with a value of 0 means that there is no piece there
		# Any index with a value of 1 means that player 1 has a piece there
		# Any index with a value of 2 means that player 2 has a piece there
		# Any index with a value of None means that a piece is not allowed
		# to be placed there (the index is neither on an intersection or corner)
		self.boardState = np.array([[   -1,     None,    None,    -1,      None,    None,    -1    ],
									[   None,   -1,      None,    -1,      None,    -1,      None  ],
									[   None,   None,    -1,      -1,      -1,      None,    None  ],
									[   -1,     -1,      -1,      None,    -1,      -1,      -1    ],
									[   None,   None,    -1,      -1,      -1,      None,    None  ],
									[   None,   -1,      None,    -1,      None,    -1,      None  ],
									[   -1,     None,    None,    -1,      None,    None,    -1    ]])


		self.adjacentPieces = {	# Outer Square Nodes
								(0, 0): [(0, 3), (3, 0)],
								(0, 3): [(0, 0), (1, 3), (0, 6)],
								(0, 6): [(0, 3), (3, 6)],
								(3, 6): [(0, 6), (3, 5), (6, 6)],
								(6, 6): [(3, 6), (6, 3)],
								(6, 3): [(6, 6), (5, 3), (6, 0)],
								(6, 0): [(6, 3), (3, 0)],
								(3, 0): [(6, 0), (3, 1), (0, 0)],

								(1, 1): [(1, 3), (3, 1)],
								(1, 3): [(1, 1), (2, 3), (0, 3), (1, 5)],
								(1, 5): [(1, 3), (3, 5)],
								(3, 5): [(1, 5), (3, 4), (3, 6), (5, 5)],
								(5, 5): [(3, 5), (5, 3)],
								(5, 3): [(5, 5), (4, 3), (6, 3), (5, 1)],
								(5, 1): [(5, 3), (3, 1)],
								(3, 1): [(5, 1), (3, 2), (3, 0), (1, 1)],

								(2, 2): [(3, 2), (2, 3)],
								(2, 3): [(2, 2), (1, 3), (2, 4)],
								(2, 4): [(2, 3), (3, 4)],
								(3, 4): [(2, 4), (3, 5), (4, 4)],
								(4, 4): [(3, 4), (4, 3)],
								(4, 3): [(4, 4), (5, 3), (4, 2)],
								(4, 2): [(4, 3), (3, 2)],
								(3, 2): [(4, 2), (3, 1), (2, 2)],
								}
		
		self.gameState = GameStage.STOPPED


	# Sets the board to all its initial values and starts the game
	def startGame(self):
		# Represents whose turn it is
		# 0 indexed so for example, a value of 0 means it's player 1's turn
		self.current_turn = 0

		# The total number of pieces that each player has
		self.total_pieces = 0

		# Records which player was the first to make a jare in the placement stage
		self.firstToJare = None

		# Changes the game to the placement stage
		self.gameState = GameStage.PLACEMENT

		self.gameRunning = True

		return self.gameRunning

	# Ends the game
	def endGame(self):
		print("Game over")

		self.gameRunning = False
		self.gameEnded.emit()


	# Generates a new QGraphicsScene based on the current state of the board
	def drawBoard(self):
		# Create a new empty scene
		scene = QGraphicsScene()

		# Create pen and brush for drawing board
		pen = QPen(self.COLOR_BLACK, self.PEN_WIDTH)
		brush = QBrush(QColor(100, 86, 30))

		# Add all the lines connecting the corners/intersections
		for rootPiece, connectedPieces in self.adjacentPieces.items():
			x1 = rootPiece[0]
			y1 = rootPiece[1]

			for piece in connectedPieces:
				x2 = piece[0]
				y2 = piece[1]

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

		# # TESTING ONLY
		# self.gamePieces[0][0] = GamePiece(self, self.GRID_SPACING, self.GRID_SPACING, self.RADIUS, self.COLOR_RED)
		# self.gamePieces[0][0].activate()
		# scene.addItem(self.gamePieces[0][0])

		self.scene = scene

		# Return the finished scene
		return scene

	# Places a new game piece on the board at the scene coordinates (x, y)
	def placePiece(self, x, y):
		if self.gameState == GameStage.PLACEMENT:
			validSpot = self.isValidSpot(x, y)

			if validSpot == None:
				print("Please press on a valid spot")
				return

			print("Player " + str(self.current_turn + 1) + "'s turn. Piece " + str(self.total_pieces + 1))
			
			board_x, board_y = self.sceneToBoard(x, y)

			# print("Placing piece at:")
			# print(validSpot[0], validSpot[1])

			self.gamePieces[self.current_turn].append(GamePiece(self, validSpot[0], validSpot[1], self.RADIUS, self.playerColors[self.current_turn]))
			
			# Adds the new game piece to the scene
			self.scene.addItem(self.gamePieces[self.current_turn][self.total_pieces])

			# Update the board's state
			self.boardState[board_y][board_x] = self.current_turn

			# Check if they are the first player to make a jare
			if self.madeNewJare() and self.firstToJare == None:
				self.firstToJare = self.current_turn
				print("The first to a jare is player " + str(self.firstToJare + 1))

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
				self.changeStage(GameStage.REMOVAL)

	# Removes game piece from scene and list of pieces
	def removePiece(self, x, y):
		if (self.gameState == GameStage.REMOVAL):
			board_x, board_y = self.sceneToBoard(x, y)
			scene_x, scene_y = self.boardToScene(board_x, board_y)

			player = self.boardState[board_y][board_x]

			# Checks if the spot clicked contains another player's piece
			if player == None or player == -1 or player == self.current_turn:
				print("Please click on another player's piece")
				return

			pieceRemoved = False
			for piece in self.gamePieces[player]:
				# If there is a piece where the player clicked
				if piece != None and piece.x == scene_x and piece.y == scene_y:
					# Empty from pieces array
					self.gamePieces[player].remove(piece)
					
					# Remove from board scene
					self.scene.removeItem(piece)

					# Update the board state
					self.boardState[board_y][board_x] = -1

					# Delete game piece
					del piece

					# Update the remaining pieces of the other player
					self.remainingPieces[player] -= 1

					# End the game if one of the players won
					if(self.isGameOver()):
						self.endGame()
						return

					pieceRemoved = True
					break

			if pieceRemoved:
				print("Successfully removed a piece")

				if self.firstRemoval:
					self.current_turn = (self.current_turn + 1) % self.TOTAL_PLAYERS

					if self.current_turn == self.firstToJare:
						# TODO: find out which player starts after the first removal stage
						self.current_turn %= self.TOTAL_PLAYERS

						self.changeStage(GameStage.MOVEMENT)

				else:
					self.changeStage(GameStage.MOVEMENT)


	# Takes in a game piece's x and y then returns the closest valid position for it to move to
	# Returns None if there is no nearby valid position
	# Returns new x and y values if the position is valid
	# Snaps to grid
	def movePiece(self, old_x, old_y, new_x, new_y):
		if (self.gameState == GameStage.MOVEMENT):
			# Check if the new coordinates are at a valid spot on the board
			validSpot = self.isValidSpot(new_x, new_y)

			if validSpot == None:
				print("Please move the piece to an empty spot")
				return

			# Convert from scene to board coordinates
			old_board_x, old_board_y = self.sceneToBoard(old_x, old_y)
			new_board_x, new_board_y = self.sceneToBoard(validSpot[0], validSpot[1])

			# Check if the new spot is adjacent to the old spot
			isAdjacent = (new_board_x, new_board_y) in self.adjacentPieces[(old_board_x, old_board_y)]

			if (isAdjacent):
				# Update the board's state
				self.boardState[old_board_y][old_board_x] = -1
				self.boardState[new_board_y][new_board_x] = self.current_turn
				
				newJare = self.madeNewJare()
				print("Player " + str(self.current_turn + 1) + " made a new jare: " + str(newJare))
				
				# Goes to the removal stage if a new jare has been made
				if newJare:
					self.current_turn %= self.TOTAL_PLAYERS
					self.changeStage(GameStage.REMOVAL)

				# Go on to the next player if no jare has been made
				else:
					self.current_turn = (self.current_turn + 1) % self.TOTAL_PLAYERS

					# Deactivates movement for all the game pieces
					self.deactivateAll()

					# Activates the pieces of the next player
					self.activatePlayer(self.current_turn)

				return validSpot

			else:
				print("Please move the piece to an adjacent spot")
				return None

	@pyqtSlot(object)
	def pieceMoved(self, piece: GamePiece):
		old_x = piece.x
		old_y = piece.y
		new_x = piece.item_pos.x()
		new_y = piece.item_pos.y()

		validMove = self.movePiece(old_x, old_y, new_x, new_y)


	# Checks if the scene coordinates are on a corner/intersection or not
	def isValidSpot(self, scene_x, scene_y, isBoardCoord = False):
		true_x = scene_x/ self.GRID_SPACING
		true_y = scene_y / self.GRID_SPACING

		target_x = round(true_x)
		target_y = round(true_y)

		x_error = abs(target_x - true_x)
		y_error = abs(target_y - true_y)

		# Check if spot is near a valid corner/intersection on the board
		if (x_error > self.MARGIN_OF_ERROR and \
			y_error > self.MARGIN_OF_ERROR):
			print("Too far from corner/intersection")
			return None
		elif (target_x < 0 or target_x >= self.boardSize or \
			target_y < 0 or target_y >= self.boardSize):
			print("Outside of the game board")
			return None
		elif(self.boardState[target_y][target_x] != -1):
			# print("Not an empty spot")
			return None
		else:
			return self.boardToScene(target_x, target_y)

	# Changes the game to the next board stage and perfroms any necessary transition actions
	def changeStage(self, nextStage):
		# Empty print to create buffer space from other print messages
		print()
		# Perform a state transition
		if(nextStage == GameStage.PLACEMENT):
			print("Going to the placement stage")

		elif(nextStage == GameStage.REMOVAL):
			if self.firstRemoval:
				if self.firstToJare != None:
					self.current_turn = self.firstToJare
				else:
					# If no one made a jare in the placement stage, player 2 goes first
					self.current_turn = 1

			print("Going to the removal stage")

			self.deactivateAll()

		elif(nextStage == GameStage.MOVEMENT):
			print("Going to the movement stage")
			# self.current_turn = 0

			# Activates player 1's game pieces
			self.deactivateAll()
			self.activatePlayer(self.current_turn)
		
		# Another empty print for more buffer space
		print()

		# Update the game state
		self.gameState = nextStage

	# Deactivates movement for all the player pieces
	def deactivateAll(self):
		for i in range(self.TOTAL_PLAYERS):
			for piece in self.gamePieces[i]:
				piece.deactivate()

	# Activates the game pieces of the current player
	# while deactivating the pieces of all the other players
	def activatePlayer(self, player):
		isActive = False

		for i in range(self.TOTAL_PLAYERS):
			# Activates the current player's pieces
			if i == player:
				for piece in self.gamePieces[player]:
					board_x, board_y = self.sceneToBoard(piece.x, piece.y)
					if self.getPossibleMoves(board_x, board_y):
						isActive = True
						self.activePieces[player] += 1
						piece.activate()

		if not isActive:
			print("Player " + str(player + 1) + " can't make any moves. \
					Player " + str(player) + " needs to move a piece")

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

	# Checks if any player has satisfied the win condition
	def isGameOver(self):
		for i in self.remainingPieces:
			if i <= 2:
				return True

		return False

	# TODO: finish implementing
	def getPossibleMoves(self, board_x, board_y):
		# Stores all the possible moves of the piece
		# 0 means a piece can't move to that index
		# 1 means a piece can move to that index
		possibleMoves = []

		for adjacentSpot in self.adjacentPieces[(board_x, board_y)]:
			spot_x, spot_y = self.boardToScene(adjacentSpot[0], adjacentSpot[1])
			if self.isValidSpot(spot_x, spot_y):
				possibleMoves.append(adjacentSpot)

		return possibleMoves

	# Searches the board and returns if a new jare was made or not
	def madeNewJare(self):
		piecesInJare = []
		neighboringAlly = None
		totalJare = 0


		# Get the indices of the player's pieces
		indices = np.where(self.boardState == self.current_turn)

		# Goes through each of the player's pieces
		for i in range(len(indices[0])):
			board_coord = (indices[1][i], indices[0][i])

			# Checks if the piece is already in another "jare"
			if board_coord in piecesInJare:
				print("The game piece at " + str(board_coord) + " is already a part of a jare\n")
				continue

			print("Investigating the game piece at " + str(board_coord))
			# Checks if any adjacent pieces are also one of the player's pieces
			for neighbor_coord in self.adjacentPieces[board_coord]:
				
				if neighbor_coord in piecesInJare:
					print("The neighbor at " + str(neighbor_coord) + " is already in a jare\n")

				elif self.boardState[neighbor_coord[1]][neighbor_coord[0]] == self.current_turn:
					if neighboringAlly == None:
						neighboringAlly = neighbor_coord
					else:
						print("Found a jare made of the pieces at " + str(board_coord) +
								 ", " + str(neighbor_coord) + ", " + str(neighboringAlly) + "\n")
						totalJare += 1

						# Record all the pieces that make up this jare
						piecesInJare.append(board_coord)
						piecesInJare.append(neighbor_coord)
						piecesInJare.append(neighboringAlly)

						# Reset the neighboring ally
						neighboringAlly = None

						print()
						break
					
			# Reset the neighboring ally
			neighboringAlly = None
				
		if self.currentJare[self.current_turn] < totalJare:
			self.currentJare[self.current_turn] = totalJare
			# print(self.boardState)
			return True

		else:
			self.currentJare[self.current_turn] = totalJare
			return False