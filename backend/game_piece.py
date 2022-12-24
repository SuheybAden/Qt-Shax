import typing
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QPen, QColor, QBrush
from backend import board_manager

class GamePiece(QGraphicsItem):
    def __init__(self, x, y, radius) -> None:
        super().__init__()
        self.x = x
        self.y = y
        self.radius = radius
        self.updateRect()
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        self.item_pos = None

    
    def updateRect(self):
        self.rect = QRectF(self.x - self.radius, self.y - self.radius / 2,
                            self.radius * 2, self.radius)

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget):
        # TODO: find out how to use custom pen and brush with drawEllipse()
        pen = QPen(QColor(0, 0, 0), 2)
        brush = QBrush(QColor(100, 86, 30))

        painter.drawEllipse(self.rect)

    def itemChange(self, change: 'QGraphicsItem.GraphicsItemChange', value: typing.Any) -> typing.Any:
        if (change == QGraphicsItem.ItemPositionChange):

            print("Item has been moved")
            self.item_pos = value

        return super().itemChange(change, value)

    

    # def mousePressEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
    #     print("Game piece pressed")
    #     self.moving = True
    #     # return super().mousePressEvent(event)

    # def mouseMoveEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
    #     print("Game piece moved")
        
    #     if self.moving:

    #         self.x = event.scenePos().x()
    #         self.y = event.scenePos().y()
    #         self.updateRect()
    #         self.update()

    #     return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        print("Game piece released")
        self.stoppedMoving = True

        if self.item_pos == None:
            print("Item position is null")
            return

        newPos = board_manager.getValidPosition(self.x, self.y,
                                 self.item_pos.x(), self.item_pos.y())
        
        if newPos != None:
            self.x = newPos[0]
            self.y = newPos[1]

        self.setPos(self.x, self.y)

        # board_manager.getBoardPos()
        self.update()

        return super().mouseReleaseEvent(event)