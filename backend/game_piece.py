import typing
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsEllipseItem
from PyQt5.QtCore import QRectF, QPointF
from PyQt5.QtGui import QPen, QColor, QBrush
from backend import board_manager

class GamePiece(QGraphicsItem):
    def __init__(self, board, x, y, radius, color) -> None:
        super().__init__()
        self.board = board
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color

        # Move item to starting position
        self.setPos(self.x, self.y)

        self.item_pos = QPointF(x, y)

    # Gets the bounding rect of the item in item coordinates
    def boundingRect(self):
        return QRectF(-self.radius, -self.radius / 2,
                            self.radius * 2, self.radius)

    # Paints the item to the scene
    def paint(self, painter, option, widget):
        rect = self.boundingRect()

        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.setBrush(QBrush(self.color))

        painter.drawEllipse(rect)

    # Makes game piece movable
    def activate(self):
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

    # Makes game piece unmovable
    def deactivate(self):
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)

    # Updates the item position if the game piece is being moved around
    def itemChange(self, change: 'QGraphicsItem.GraphicsItemChange', value: typing.Any) -> typing.Any:
        if (change == QGraphicsItem.ItemPositionChange):
            self.item_pos = value

        return super().itemChange(change, value)

    # Places the game piece in the nearest corner/intersection on the game board
    # Otherwise, it will move the game piece back to its original position
    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:

        # # Handles edge case where the mouse was released before the game piece was moved
        # # aka the game piece was just quickly clicked
        # if self.item_pos == None:
        #     print("Item position is null")
        #     return

        newPos = self.board.movePiece(self.x, self.y,
                                 self.item_pos.x(), self.item_pos.y())
        
        if newPos != None:
            self.x = newPos[0]
            self.y = newPos[1]

        self.setPos(self.x, self.y)

        return super().mouseReleaseEvent(event)