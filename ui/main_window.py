from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtGui import QPen, QColor, QBrush, QTransform, QMovie, QPixmap
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsEllipseItem, QMessageBox, QGraphicsPixmapItem, QLabel
from PyQt5.QtCore import QEvent, Qt, pyqtSlot, pyqtSignal, QVariant, QSettings, QSize

from PyQt5 import QtCore

from backend.board_manager import BoardManager, GameStage
from backend.game_piece import GamePiece

from .settings_window import SettingsWindow

import numpy as np
import os


class MainWindow(QtWidgets.QMainWindow):

    # ************************************* INIT METHODS ******************************************
    def __init__(self) -> None:
        super().__init__()

        self.loading_gif_path = "images/loading.gif"

        # Load application settings
        self.settings = QSettings("SA LLC", "Qt Shax")
        self.settings.clear()

        self.MARGIN_OF_ERROR = float(self.settings.value("marginOfError", 0.2))
        self.mode = self.settings.value("mode", "remote")

        minPieces = int(self.settings.value("minPieces", 2))
        maxPieces = int(self.settings.value("maxPieces", 10))
        url = self.settings.value("url", "ws://localhost:8765")

        # Start up a local game manager to setup the initial board
        self.boardManager = BoardManager(minPieces, maxPieces, url)

        # Tracks the game piece graphicItems on the board
        self.gamePieces = {}

        # Initialize the UI and signal-slot connections
        self.load_ui()
        self.connect_all()

    # Loads the Qt UI file with the same name
    def load_ui(self):
        cwd = os.getcwd()
        filename = os.path.splitext(os.path.basename(__file__))[0]
        uic.loadUi(cwd + "/ui_files/" + filename + ".ui", self)

        # Add a blank scene to the graphics view
        self.graphicsView.setScene(QGraphicsScene())

    # Connects all the signals and slots
    def connect_all(self):
        # Connect UI elements
        self.gameBtn.clicked.connect(self.gameBtn_Clicked)
        self.settingsAction.triggered.connect(self.settingsAction_Triggered)

        # Connect signals from the board manager
        self.boardManager.connected.connect(self.connected_to_board)
        self.boardManager.gameEnded.connect(self.boardManager_GameEnded)

        self.boardManager.startGameEvaluated.connect(self.startGame_Response)
        self.boardManager.placePieceEvaluated.connect(self.placePiece_Evaluated)
        self.boardManager.removePieceEvaluated.connect(self.removePiece_Evaluated)
        self.boardManager.movePieceEvaluated.connect(self.movePiece_Evaluated)
        self.boardManager.endEvaluated.connect(self.end_Evaluated)

    @pyqtSlot()
    def connected_to_board(self):
        self.announcementLbl.setText("Connected to Server")

    def closeEvent(self, event):
        del self.boardManager
        event.accept()

    def update_on_screen_text(self, next_state, next_player, msg):
        if next_player == self.boardManager.player_num:
            self.announcementLbl.setText("Your Turn!")
        else:
            self.announcementLbl.setText("Opponent's Turn.")

        # self.p1PiecesLbl.setText(str(num_p1_pieces))
        # self.p2PiecesLbl.setText(str(num_p2_pieces))


    # ************************* INIT METHODS FOR THE GAME BOARD ***************
    # Draws the initial state of the board
    @pyqtSlot()
    def initGraphics(self, adjacentPieces):
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
        self.drawBoard(adjacentPieces)

        print("Initialized the graphics")

    # Generates a new QGraphicsScene based on the current state of the board
    def drawBoard(self, adjacentPieces):
        # Create a new empty scene
        scene = QGraphicsScene()

        # Create the pens and brush for drawing the board
        linesPen = QPen(self.COLOR_BLACK, self.PEN_WIDTH)
        intersectionsPen = QPen(QColor(150, 126, 45), self.PEN_WIDTH)
        brush = QBrush(QColor(100, 86, 30))

        # Add all the corners/intersections and their connecting lines
        for rootPiece, connectedPieces in adjacentPieces.items():
            x1 = rootPiece[0]
            y1 = rootPiece[1]

            for piece in connectedPieces:
                x2 = piece[0]
                y2 = piece[1]

                scene.addLine(x1 * self.GRID_SPACING, y1 * self.GRID_SPACING,
                              x2 * self.GRID_SPACING, y2 * self.GRID_SPACING, linesPen)

        for rootPiece, connectedPieces in adjacentPieces.items():
            x = rootPiece[0] * self.GRID_SPACING
            y = rootPiece[1] * self.GRID_SPACING
            scene.addEllipse(x - self.RADIUS, y - self.RADIUS,
                             self.RADIUS * 2, self.RADIUS * 2,
                             intersectionsPen, brush)

        # Show the scene in the graphics view
        self.scene = scene
        self.graphicsView.setScene(scene)
        self.graphicsView.installEventFilter(self)

        print("Finished drawing the board.")

    # ****************************** UI EVENTS *************************************************
    # Event filter for the QGraphicsScene displaying the game board
    # Responsible for alerting the board manager of a piece placement or removal

    def eventFilter(self, obj: 'QObject', event: 'QEvent') -> bool:
        # Check if it is a mouse press event
        # Removes or places a piece depending on the current game stage
        if event.type() == QEvent.MouseButtonPress:
            pos = self.graphicsView.mapToScene(event.pos())

            if self.boardManager.gameState == GameStage.PLACEMENT:
                # Convert to board coordinates
                x, y = self.sceneToBoard(pos.x(), pos.y())

                if x < 0 or y < 0:
                    self.announcementLbl.setText("Please click on a valid node")
                    return True
                
                # Send the piece placement move to the board
                self.boardManager.placePiece(x, y)

            elif self.boardManager.gameState == GameStage.REMOVAL or \
                    self.boardManager.gameState == GameStage.FIRST_REMOVAL:
                # Get the game piece at the board coordinates
                piece = self.scene.itemAt(pos.x(), pos.y(), self.graphicsView.transform())

                if not isinstance(piece, GamePiece):
                    self.announcementLbl.setText("Please click on a game piece")

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

    # Alerts the board manager that the user either wants to start or end a game
    @pyqtSlot()
    def gameBtn_Clicked(self):
        # Tries to end the game
        if (self.boardManager.running or self.boardManager.waiting):
            self.boardManager.end()
            self.gameBtn.setText("New Game")
            return

        # Tries to start a game
        else:
            self.boardManager.startGame()

    # Opens the settings window
    @pyqtSlot()
    def settingsAction_Triggered(self):
        print("button triggered")
        if (self.boardManager.gameState != GameStage.STOPPED):
            print("Message appeared")
            QMessageBox.critical(self, "Ongoing Game",
                                 "The current game must be finished before editing the settings.")

        else:
            print("Settings opened")
            settingsWindow = SettingsWindow(self.settings)
            if (settingsWindow.exec()):
                print("Your settings were saved!")

    # **************************** GAME EVENTS *************************************
    # Starts up a game

    @pyqtSlot(bool, str, bool, dict)
    def startGame_Response(self, success, error, waiting, adjacentPieces):
        if not success:
            print("Error: " + error)
            return

        # Play the loading screen while the player is in the waiting list
        if waiting:
            # Load GIF
            loading_gif = QLabel()
            loading_gif.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

            movie = QMovie(self.loading_gif_path)
            movie.setScaledSize(QSize(100, 100))

            loading_gif.setMovie(movie)
            movie.start()

            # Add loading GIF to graphics view
            scene = QGraphicsScene()
            self.loading_widget = scene.addWidget(loading_gif)
            self.graphicsView.setScene(scene)

            # Update on-screen text
            self.announcementLbl.setText("Waiting for a game...")
            self.printLbl.setText("")
            self.gameBtn.setText("Quit")

        # If the game has started
        else:
            self.announcementLbl.setText("Started a new game!")
            self.printLbl.setText("Click on a node to place a piece")
            self.gameBtn.setText("Quit")
            self.initGraphics(adjacentPieces)

    # Updates the board visuals after the board manager evaluates the piece placement request
    @pyqtSlot(bool, str, int, int, int, str, int)
    def placePiece_Evaluated(self, success, error, ID, x, y, nextStage, nextPlayer):


        # Check if the piece placement has been approved
        if not success:
            print("The piece couldn't be placed")
            print(error)
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

        if (nextStage == "PLACEMENT"):
            self.printLbl.setText("Click on a node to place piece")
        elif (nextStage == "REMOVAL" or nextStage == "FIRST_REMOVAL"):
            self.printLbl.setText("Click on a piece to remove")

    # Updates the board visuals after the board manager evaluates the piece removal request

    @pyqtSlot(bool, str, int, str, int, list)
    def removePiece_Evaluated(self, success, error, ID, nextStage, nextPlayer, activePieces):

        if nextPlayer == self.boardManager.player_num:
            self.announcementLbl.setText("Your Turn!")
        else:
            self.announcementLbl.setText("Opponent's Turn.")

        if not success:
            print("The piece couldn't be removed")
            print(error)
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
            self.printLbl.setText("Drag one of your pieces to an adjacent spot")

        elif (nextStage == "removal"):
            self.printLbl.setText("Click on a piece to remove")

    # Updates the board visuals after the board manager evaluates the piece movement request

    @pyqtSlot(bool, str, int, int, int, str, int, list)
    def movePiece_Evaluated(self, success, error, ID, x, y, nextStage, nextPlayer, activePieces):

        if nextPlayer == self.boardManager.player_num:
            self.announcementLbl.setText("Your Turn!")
        else:
            self.announcementLbl.setText("Opponent's Turn.")

        # Get the piece corresponding to the evaluated piece movement
        piece = self.gamePieces[ID]

        # If piece movement was not approved, move the piece back to its original position
        if not success:
            print("The piece couldn't be moved")
            print(error)
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
            self.printLbl.setText("Drag one of your pieces to an adjacent spot")

        elif (nextStage == "removal"):
            self.printLbl.setText("Click on a piece to remove")

    @pyqtSlot(bool, str, bool, bool)
    def end_Evaluated(self, success, msg, won, waiting):
        if not success:
            print(msg)
            return

        if waiting:
            scene = self.graphicsView.scene()
            scene.removeItem(self.loading_widget)

        self.announcementLbl.setText(msg)

    # Updates the board visuals after the game ends
    @pyqtSlot()
    def boardManager_GameEnded(self):
        self.announcementLbl.setText("Game Over")
        self.gameBtn.setText("New Game")

    # **************************** BOARD-SCENE TRANSLATIONS **************************
    # Translates the scene's x and y coordinates to the nearest board index

    def sceneToBoard(self, x: float, y: float):
        raw_x: float = x / self.GRID_SPACING
        raw_y: float = y / self.GRID_SPACING

        error_x: float = abs(round(raw_x) - raw_x)
        error_y: float = abs(round(raw_y) - raw_y)

        # Check if spot is near a valid node on the board
        if (error_x > self.MARGIN_OF_ERROR and
                error_y > self.MARGIN_OF_ERROR):
            return (-1, -1)

        return (round(raw_x), round(raw_y))

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
