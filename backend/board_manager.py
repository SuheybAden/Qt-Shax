import json
import sys
import numpy as np
from enum import Enum

from PyQt5.QtWebSockets import QWebSocket, QWebSocketProtocol
from PyQt5.QtWidgets import QApplication, QWidget, QShortcut
from PyQt5.QtCore import QUrl, QTimer, Qt, pyqtSlot, pyqtSignal, QVariant, QObject

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
    connected = pyqtSignal()

    gameStarted = pyqtSignal(QVariant)
    gameEnded = pyqtSignal()

    startGameEvaluated = pyqtSignal(bool, str, bool, str, int, dict)
    placePieceEvaluated = pyqtSignal(bool, str, int, int, int, str, int)
    removePieceEvaluated = pyqtSignal(bool, str, int, str, int, list)
    movePieceEvaluated = pyqtSignal(bool, str, int, int, int, str, int, list)
    endEvaluated = pyqtSignal(bool, str, bool, bool)

    def __init__(self, minPieces, maxPieces, url) -> None:
        super().__init__()

        # ********************** SETTING VALUES ******************************
        # Total number of players
        self.TOTAL_PLAYERS = 2

        # Maximum number of pieces each player can have
        self.MAX_PIECES = minPieces

        # Minimum number of pieces a player can have or its game over
        self.MIN_PIECES = maxPieces

        # How far off a piece can be from the center of its new location
        # Goes from 0 to 1
        self.MARGIN_OF_ERROR = .2

        # How far the pieces' ID needs to bit shifted to the left to store the player ID with it
        self.ID_SHIFT = 2

        # ***************** GAME VARIABLES **************************
        # Tracks if a game is currently running or not
        self.running = False

        # Tracks if the manager is waiting for a game
        self.waiting = False

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

        self.player_tokens = [0, 0]

        # ********************* WEBSOCKET VARIABLES *************************
        self.websocket = QWebSocket()
        self.url = QUrl(url)
        self.status = False

        self.connect_all()
        self.websocket.open(self.url)
        print("Opened websocket")

    def __del__(self):
        self.websocket.close(QWebSocketProtocol.CloseCode.CloseCodeAbnormalDisconnection)
        print("Closing connection")

    # Connects the appropriate signals and slots
    def connect_all(self):
        self.websocket.connected.connect(self.on_connected)
        self.websocket.textMessageReceived.connect(self.onTextMessageReceived)
        self.websocket.error.connect(self.on_error)

    # Runs once there's an established connection with the WebSocket server
    def on_connected(self):
        print("Connected to server")
        self.status = True

        # Let the UI know that a connection has been made
        self.connected.emit()

    def on_error(self, error_code):
        print(f"Error: {error_code}")

    # Sends a JSON message to the WebSocket server
    def sendMessage(self, message):
        self.websocket.sendTextMessage(json.dumps(message))
        # if self.status:
        # else:
        #     print("Not connected to server yet")

    # Receives a JSON response from the WebSocket server
    # Routes it to the appropriate response function
    def onTextMessageReceived(self, message):
        # DEBUG PRINT
        data = json.loads(message)
        print(f"\nReceived message: {json.dumps(data, indent=4)}")

        # Pass the response to the appropriate handler
        action = data["action"]
        if action == "join_game":
            self.startGame_Response(data)
        elif action == "end":
            self.end_Response(data)
        elif action == "place_piece":
            self.placePiece_Response(data)
        elif action == "remove_piece":
            self.removePiece_Response(data)
        elif action == "move_piece":
            self.movePiece_Response(data)

    # Sends a request for a game to be started to the shax API
    @pyqtSlot()
    def startGame(self):
        # Allow players to join different types of games
        message = {"action": "join_game",
                   "game_type": 1}
        self.sendMessage(message)

    # Handles the response data from the shax API when a startGame action is sent
    def startGame_Response(self, data):
        # Check that the response contains all the required keys
        required_keys = ("success", "waiting")
        if not all(key in data for key in required_keys):
            print("Received an unexpected response from the websocket server.")
            return

        # Load all the game parameters
        success: bool = data["success"]
        error: str = data["error"]
        self.waiting: bool = data["waiting"]
        self.player_num = data["player_num"]
        print(data["player1_key"])
        print(data["player2_key"])
        self.player_tokens[0] = data["player1_key"]
        self.player_tokens[1] = data["player2_key"]
        gameState = data["next_state"]
        self.current_turn = data["next_player"]

        # Update the game state
        self.gameState = GameStage[gameState]

        # Check if the game started successfully
        if success:
            self.running = True

        # Convert the adjacent pieces array back to a python dict
        adjacentPieces_raw: dict | None = data["adjacent_pieces"]
        adjacentPieces = {tuple(int(val) for val in key.strip('()').split(',')): [[int(val1), int(val2)] for val1, val2 in value]
                          for key, value in adjacentPieces_raw.items()}

        # Notifies the main window about the outcome of the start game request
        self.startGameEvaluated.emit(success, error, self.waiting, gameState, self.current_turn, adjacentPieces)
        return

    # Places a new game piece on the board at the scene coordinates (x, y)
    @pyqtSlot(float, float)
    def placePiece(self, x, y):
        print("Attempting to place a piece...")
        print(self.player_tokens)
        message = {"action": "place_piece",
                   "x": x,
                   "y": y,
                   "player_key": self.player_tokens[self.current_turn]}
        self.sendMessage(message)

    def placePiece_Response(self, data):
        try:
            success: bool = data["success"]
            next_state: str = data["next_state"]
            next_player: int = data["next_player"]

            # Updates the game state
            self.gameState = getattr(GameStage, next_state, self.gameState)
            self.current_turn = next_player

            # Only return the error msg if the move failed
            if not success:
                error: str = data["error"]
                self.placePieceEvaluated.emit(success, error, 0, 0, 0, "", 0)
            else:
                # Load the rest of the response data
                ID: int = data["new_piece_ID"]
                x: int = data["new_x"]
                y: int = data["new_y"]

                # Notifies the UI about the moves outcome
                self.placePieceEvaluated.emit(success, "", ID, x, y, next_state, self.current_turn)
        except Exception as e:
            print("Received an unexpected response: ", e)

    # Removes game piece from scene and list of pieces
    @pyqtSlot(int)
    def removePiece(self, pieceID):
        print("Attempting to remove a piece...")
        message = {"action": "remove_piece",
                   "piece_ID": pieceID,
                   "player_key": self.player_tokens[self.current_turn]}
        self.sendMessage(message)

    def removePiece_Response(self, data):
        try:
            success: bool = data["success"]
            next_state: str = data["next_state"]
            next_player: int = data["next_player"]

            # Updates the game state
            self.gameState = getattr(GameStage, next_state, self.gameState)
            self.current_turn = next_player

            # If the move failed, only return the error msg
            if not success:
                error: str = data["error"]
                self.removePieceEvaluated.emit(success, error, 0, next_state, self.current_turn, [])

            else:
                # Check if the game has finished
                if "game_over" in data:
                    # TODO: handle the game ending
                    pass

                # Load the rest of the response data
                ID: int = data["removed_piece"]
                active_pieces: list = data["active_pieces"]

                # Notify the UI about the results
                self.removePieceEvaluated.emit(
                    success, "", ID, next_state, self.current_turn, active_pieces)

        except Exception as e:
            print("Received an unexpected response: ", e)

    # Takes in a game piece's x and y
    # Returns None if there is no nearby valid position
    # Returns new x and y values if the position is valid
    # Snaps to grid
    @pyqtSlot(int, float, float)
    def movePiece(self, ID, new_x, new_y):
        print("Attempting to remove a piece...")
        message = {"action": "move_piece",
                   "piece_ID": ID,
                   "new_x": new_x,
                   "new_y": new_y,
                   "player_key": self.player_tokens[self.current_turn]}
        self.sendMessage(message)

    def movePiece_Response(self, data):
        try:
            success: bool = data["success"]
            next_state: str = data["next_state"]
            next_player: int = data["next_player"]

            # Updates the game state
            self.gameState = getattr(GameStage, next_state, self.gameState)
            self.current_turn = next_player

            if not success:
                error: str = data["error"]
                self.movePieceEvaluated.emit(success, error, 0, 0, 0,
                                             next_state, self.current_turn, [])

            else:
                # Loads the rest of the response data
                ID: int = data["moved_piece"]
                x: float = data["new_x"]
                y: float = data["new_y"]
                active_pieces: int = data["active_pieces"]

                # Notifies the UI
                self.movePieceEvaluated.emit(
                    success, "", ID, x, y, next_state, self.current_turn, active_pieces)
        except Exception as e:
            print("Received an unexpected response: ", e)

    @pyqtSlot()
    def end(self):
        message = {"action": "end"}
        self.sendMessage(message)

    def end_Response(self, data: dict):
        try:
            success = data["success"]
            msg = data["msg"]
            won = data.get("won", False)

            self.endEvaluated.emit(success, msg, won, self.waiting)

            self.running = False
            self.waiting = False

        except Exception as e:
            print("Received an unexpected response: ", e)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = QWidget()
    client = BoardManager()
    # client.startGame()

    # Send a message every 5 seconds
    timer = QTimer()
    timer.timeout.connect(lambda: client.startGame())
    timer.start(5000)

    shortcut = QShortcut(Qt.CTRL + Qt.Key_C, widget)
    shortcut.activated.connect(app.quit)

    widget.show()
    sys.exit(app.exec_())
