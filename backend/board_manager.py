from enum import Enum
import numpy as np

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QVariant
from PyQt5 import Qt

# Enum for tracking what stage the game is in
# TODO: Come up with a better name for the 'MOVEMENT' game stage
class GameStage(Enum):
	STOPPED = 0
	PLACEMENT = 1
	FIRST_REMOVAL = 2
	REMOVAL = 3
	MOVEMENT = 4

class BoardManager(QObject):
	# *************** SIGNALS
	gameStarted = pyqtSignal(QVariant)
	gameEnded = pyqtSignal()

	placePieceEvaluated = pyqtSignal(bool, int, float, float, str, int)
	removePieceEvaluated = pyqtSignal(bool, int, str, int, list)
	movePieceEvaluated = pyqtSignal(bool, int, float, float, str, int, list)

	# Constructor function
	def __init__(self) -> None:
		super().__init__()

		# ************** SETTING VALUES ******************************
		# Total number of players
		self.TOTAL_PLAYERS = 2

		# Maximum number of pieces each player can have
		self.MAX_PIECES = 5

		# Minimum number of pieces a player can have or its game over
		self.MIN_PIECES = 2

		# How far of a piece can be from the center of its new location
		# Goes from 0 to 1
		self.MARGIN_OF_ERROR = .2

		# How far the pieces' ID needs to bit shifted to the left to store the player ID with it
		self.ID_SHIFT = 2


		# ***************** GAME VARIABLES **************************
		# Tracks if a game is currently running or not
		self.gameRunning = False

		# Tracks what stage the game is currently in
		self.gameState = GameStage.STOPPED

		# Represents whose turn it is
		# 0 indexed so for example, a value of 0 means it's player 1's turn
		self.current_turn = 0

		# Array for keeping track of how many pieces each player has
		self.total_pieces = np.zeros(self.TOTAL_PLAYERS, np.int8)

		# Tracks the ID of the player who first made a jare in the placement stage
		# Determines which player goes first in the "first_removal" stage
		self.firstToJare = None

		# Array containing the total number of "jare" each player has made
		self.currentJare = np.zeros(self.TOTAL_PLAYERS, np.int8)


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


	# Sets the board to all its initial values and starts the game
	@pyqtSlot()
	def startGame(self):
		# Sets all the game variables to their initial states

		# Player variables
		self.current_turn = 0

		# Pieces variables
		self.total_pieces = np.zeros(self.TOTAL_PLAYERS, np.int8)

		# Jare variables
		self.firstToJare = None
		self.currentJare = np.zeros(self.TOTAL_PLAYERS, np.int8)

		# Starts the game off in the placement stage
		self.gameState = GameStage.PLACEMENT

		# Starts running the game
		self.gameRunning = True

		return self.gameRunning

	# Ends the game
	@pyqtSlot()
	def endGame(self):
		# Debugging print
		print("Game over")

		self.gameState = GameStage.STOPPED
		self.gameRunning = False
		self.gameEnded.emit()


	# Places a new game piece on the board at the scene coordinates (x, y)
	@pyqtSlot(float, float)
	def placePiece(self, x, y):
		if self.gameState == GameStage.PLACEMENT:
			validSpot = self._isValidSpot(x, y)

			if validSpot == None:
				# print("Please press on a valid spot")
				return

			# print("Player " + str(self.current_turn + 1) + "'s turn. \
					# Placing piece #" + str(self.total_pieces[self.current_turn] + 1))

			# Generate an ID for the new game piece
			newID = (self.total_pieces[self.current_turn] << self.ID_SHIFT) | self.current_turn

			# Update the board's state
			self.boardState[y][x] = newID
			
			# Updating the player's total number of peices
			self.total_pieces[self.current_turn] += 1

			# Check if they are the first player to make a jare
			if self._madeNewJare() and self.firstToJare == None:
				self.firstToJare = self.current_turn
				print("The first to a jare is player " + str(self.firstToJare + 1))

			# Go to the next player's turn
			self.current_turn = (self.current_turn + 1) % self.TOTAL_PLAYERS

			nextStage = "placement"
			# If all the pieces have been placed,
			# go on to the second stage of the game
			if np.all(self.total_pieces >= self.MAX_PIECES):
				self._changeStage(GameStage.FIRST_REMOVAL)
				nextStage = "removal"

			
			self.placePieceEvaluated.emit(True, newID, x, y, nextStage, self.current_turn)

	# Removes game piece from scene and list of pieces
	@pyqtSlot(int)
	def removePiece(self, pieceID):
		if (self.gameState == GameStage.REMOVAL or self.gameState == GameStage.FIRST_REMOVAL):
			player = pieceID & (2**self.ID_SHIFT - 1)

			# Checks if the piece exists on the board
			if pieceID not in self.boardState:
				# print("This piece doesn't exist")
				return

			# Checks if the spot clicked contains another player's piece
			if player == self.current_turn:
				# print("Please click on another player's piece")
				return

			# Remove the piece from the board
			self.boardState[self.boardState == pieceID] = -1

			# Update the remaining pieces of the other player
			self.total_pieces[player] -= 1

			# End the game if one of the players won
			if(self._isGameOver()):
				self.removePieceEvaluated.emit(True, pieceID, "removal", self.current_turn, [])
				self.endGame()
				return

			# print("Removed piece from board manager")
			activePieces = []
			nextStage = "removal"
			# If this is the very first removal stage,
			# every player must have a chance to remove a piece before going on to the movement stage
			
			if self.gameState == GameStage.FIRST_REMOVAL:
				self.current_turn = (self.current_turn + 1) % self.TOTAL_PLAYERS

				if (self.firstToJare == None and self.current_turn == 1) or \
					(self.current_turn == self.firstToJare):
					# TODO: find out which player starts after the first removal stage
					self._changeStage(GameStage.MOVEMENT)
					nextStage = "movement"
					activePieces = self._getActivePieces()

			else:
				self._changeStage(GameStage.MOVEMENT)
				nextStage = "movement"
				activePieces = self._getActivePieces()

			
			self.removePieceEvaluated.emit(True, pieceID, nextStage, self.current_turn, activePieces)


	# Takes in a game piece's x and y
	# Returns None if there is no nearby valid position
	# Returns new x and y values if the position is valid
	# Snaps to grid
	@pyqtSlot(int, float, float)
	def movePiece(self, ID, new_x, new_y):
		if (self.gameState != GameStage.MOVEMENT):
			# print("Need to be in the movement stage to move the piece")
			return


		# Check if the new coordinates are at a valid spot on the board
		validSpot = self._isValidSpot(new_x, new_y)

		if validSpot == None:
			# print("Please move the piece to an empty spot")
			self.movePieceEvaluated.emit(False, ID, 0, 0, "movement", self.current_turn, list())
			return

		# Get the old coordinates of the game piece
		old_board_x, old_board_y = self._pieceIDtoCoord(ID)

		# Check if the new spot is adjacent to the old spot
		isAdjacent = validSpot in self.adjacentPieces[(old_board_x, old_board_y)]

		if (isAdjacent):
			# Update the board's state
			self.boardState[old_board_y][old_board_x] = -1
			self.boardState[validSpot[1]][validSpot[0]] = ID
			

			# newJare = False
			newJare = self._madeNewJare()
			# print("Player " + str(self.current_turn + 1) + " made a new jare: " + str(newJare))
			
			nextStage = ""
			activePieces = []
			# Gets the next game stage based on whether a new jare was made or not
			if newJare:
				self._changeStage(GameStage.REMOVAL)
				nextStage = "removal"

			# Go on to the next player if no jare has been made
			else:
				self.current_turn = (self.current_turn + 1) % self.TOTAL_PLAYERS
				nextStage = ""
				# Checks if the next player has any pieces that can be moved
				activePieces = self._getActivePieces()

				if not activePieces:
					print("Player " + str(self.current_turn + 1) + " can't move any pieces. " + 
	   						"Going back to the previous player.")
					self.current_turn = (self.current_turn - 1) % self.TOTAL_PLAYERS
					
			# Signal the UI
			self.movePieceEvaluated.emit(True, ID, validSpot[0], validSpot[1], 
						nextStage, self.current_turn, activePieces)

		else:
			# print("Please move the piece to an adjacent spot")
			self.movePieceEvaluated.emit(False, ID, 0, 0, "movement", self.current_turn, list())
			return None


	# *************************** HELPER FUNCTIONS **************************************** #

	def _pieceIDtoCoord(self, pieceID):
		# print("The pieces ID is: " + str(pieceID))
		index = np.where(self.boardState == pieceID)
		return index[1][0], index[0][0]

	# Checks if the scene coordinates are on a corner/intersection or not
	def _isValidSpot(self, x, y):
		target_x = round(x)
		target_y = round(y)

		x_error = abs(target_x - x)
		y_error = abs(target_y - y)

		# Check if spot is near a valid corner/intersection on the board
		if (x_error > self.MARGIN_OF_ERROR and \
			y_error > self.MARGIN_OF_ERROR):
			# print("Too far from corner/intersection")
			return None
		elif (target_x < 0 or target_x >= self.boardSize or \
			target_y < 0 or target_y >= self.boardSize):
			# print("Outside of the game board")
			return None
		elif(self.boardState[target_y][target_x] != -1):
			# print("Not an empty spot")
			return None
		else:
			return (target_x, target_y)

	# Changes the game to the next board stage and perfroms any necessary transition actions
	def _changeStage(self, nextStage):
		# Empty print to create buffer space from other print messages
		print()
		# Perform a state transition
		if(nextStage == GameStage.PLACEMENT):
			print("Going to the placement stage")

		elif(nextStage == GameStage.FIRST_REMOVAL):
			print(self.boardState)
			if self.firstToJare != None:
				self.current_turn = self.firstToJare
			else:
				# If no one made a jare in the placement stage, player 2 goes first
				self.current_turn = 1

			print("Going to the first removal stage")

		elif(nextStage == GameStage.REMOVAL):
			print("Going to the removal stage")

		elif(nextStage == GameStage.MOVEMENT):
			print("Going to the movement stage")
		
		# Another empty print for more buffer space
		print()

		# Update the game state
		self.gameState = nextStage

	# Takes in a piece ID and returns all the board locations that piece can move to
	def _getPossibleMoves(self, pieceID):
		# Stores all the possible moves of the piece
		# 0 means a piece can't move to that index
		# 1 means a piece can move to that index
		possibleMoves = []

		x, y = self._pieceIDtoCoord(pieceID)
		# print("Finding the possible moves for piece " + str(pieceID) + " at (" + str(x) + ", " + str(y) + ")")

		for adjacentSpot in self.adjacentPieces[(x, y)]:
			# print("Checking the adjacent spot at (" + str(x) + ", " + str(y) + ")")

			if self._isValidSpot(adjacentSpot[0], adjacentSpot[1]):
				possibleMoves.append(adjacentSpot)

		return possibleMoves

	def _getActivePieces(self):
		activePieces = []

		# Get the indices of the player's pieces
		# TODO: check if there is a better way to do this
		board_copy = np.copy(self.boardState)
		non_null = np.logical_and(board_copy != None, board_copy != -1)
		board_copy[non_null] = board_copy[non_null] & (2**self.ID_SHIFT - 1)
		indices = np.where(board_copy == self.current_turn)

		# Goes through each of the player's pieces
		for i in range(len(indices[0])):
			x = indices[1][i]
			y = indices[0][i]
			id = self.boardState[y][x]
			if self._getPossibleMoves(id):
				activePieces.append(id)

		return activePieces


	# Searches the board and returns if a new jare was made or not
	def _madeNewJare(self):
		piecesInJare = []
		neighboringAlly = None
		totalJare = 0

		# Get the indices of the player's pieces
		# TODO: check if there is a better way to do this
		board_copy = np.copy(self.boardState)
		non_null = np.logical_and(board_copy != None, board_copy != -1)
		board_copy[non_null] = board_copy[non_null] & (2**self.ID_SHIFT - 1)
		indices = np.where(board_copy == self.current_turn)

		# Goes through each of the player's pieces
		for i in range(len(indices[0])):
			board_coord = (indices[1][i], indices[0][i])

			# Checks if the piece is already in another "jare"
			if board_coord in piecesInJare:
				# print("The game piece at " + str(board_coord) + " is already a part of a jare\n")
				continue

			# print("Investigating the game piece at " + str(board_coord))
			# Checks if any adjacent pieces are also one of the player's pieces
			for neighbor_coord in self.adjacentPieces[board_coord]:
				
				if neighbor_coord in piecesInJare:
					# print("The neighbor at " + str(neighbor_coord) + " is already in a jare\n")
					continue

				elif (self.boardState[neighbor_coord[1]][neighbor_coord[0]] != -1 and
						(self.boardState[neighbor_coord[1]][neighbor_coord[0]] & (2**self.ID_SHIFT - 1) == self.current_turn)):
					if neighboringAlly == None:
						neighboringAlly = neighbor_coord
					else:
						# print("Found a jare made of the pieces at " + str(board_coord) +
								#  ", " + str(neighbor_coord) + ", " + str(neighboringAlly) + "\n")
						totalJare += 1

						# Record all the pieces that make up this jare
						piecesInJare.append(board_coord)
						piecesInJare.append(neighbor_coord)
						piecesInJare.append(neighboringAlly)

						# Reset the neighboring ally
						neighboringAlly = None

						# print()
						break
					
			# Reset the neighboring ally
			neighboringAlly = None
				
		if self.currentJare[self.current_turn] < totalJare:
			self.currentJare[self.current_turn] = totalJare
			return True

		else:
			self.currentJare[self.current_turn] = totalJare
			return False


	# Checks if any player has satisfied the win condition
	def _isGameOver(self):
		for i in self.total_pieces:
			if i <= self.MIN_PIECES:
				return True

		return False