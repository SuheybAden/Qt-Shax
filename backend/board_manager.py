from PyQt5 import QtWidgets, uic, QtGui

pieces = []
boardState = {}


def initBoard():
    pass

# Generates a new QGraphicsScene based on the current state of the board
def drawBoard():
    # Create a new empty scene
    scene = QtWidgets.QGraphicsScene()

    # TODO: draw the board in the scene

    # Return the finished scene
    return scene

# Updates the board's state based on the most recent move
def updateBoardState(move):
    updatedBoardState = {}



    return updatedBoardState


# Checks if a move violates any rules
def checkRules():
    pass