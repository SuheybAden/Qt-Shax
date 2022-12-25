import typing
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsEllipseItem
from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QPen, QColor, QBrush
from backend import board_manager

class GamePiece(QGraphicsItem):
    def __init__(self, x, y, radius, color) -> None:
        super().__init__()
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.updateShape()

        self.item_pos = None

    # Updates the bounding rect of the game piece
    def updateShape(self):
        self.rect = QRectF(self.x - self.radius, self.y - self.radius / 2,
                            self.radius * 2, self.radius)

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget):
        # TODO: find out how to use custom pen and brush with drawEllipse()
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.setBrush(QBrush(self.color))

        painter.drawEllipse(self.rect)

    def activate(self):
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

    # Updates the item position if the game piece is being moved around
    def itemChange(self, change: 'QGraphicsItem.GraphicsItemChange', value: typing.Any) -> typing.Any:
        if (change == QGraphicsItem.ItemPositionChange):

            print("Item has been moved")
            self.item_pos = value

        return super().itemChange(change, value)

    # Places the game piece in the nearest corner/intersection on the game board
    # Otherwise, it will move the game piece back to its original position
    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        print("Game piece released")
 
        # Handles edge case where the mouse was released before the game piece was moved
        # aka the game piece was just quickly clicked
        if self.item_pos == None:
            print("Item position is null")
            return

        newPos = board_manager.getValidPosition(self.x, self.y,
                                 self.item_pos.x(), self.item_pos.y())
        
        if newPos != None:
            print("Found a valid position")
            self.x = newPos[0]
            self.y = newPos[1]

        self.setPos(self.x, self.y)

        # board_manager.getBoardPos()
        self.update()

        return super().mouseReleaseEvent(event)