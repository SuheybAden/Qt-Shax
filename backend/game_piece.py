import typing
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsEllipseItem, QGraphicsObject
from PyQt5.QtCore import QRectF, QPointF, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QPen, QColor, QBrush
from backend import board_manager

class GamePiece(QGraphicsObject):
	# *************** SIGNALS
	pieceMoved = pyqtSignal(int, float, float)

	def __init__(self, ID, x, y, radius, color) -> None:
		super().__init__()
		self.ID = ID
		self.x = x
		self.y = y
		self.radius = radius
		self.color = color

		self.activated = False

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

		if self.activated:
			painter.setPen(QPen(QColor(0, 150, 0), 2))
		else:
			painter.setPen(QPen(QColor(0, 0, 0), 2))

		painter.setBrush(QBrush(self.color))

		painter.drawEllipse(rect)

	# Makes game piece movable
	def activate(self):
		self.setFlag(QGraphicsItem.ItemIsMovable)
		self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

		self.activated = True

	# Makes game piece unmovable
	def deactivate(self):
		self.setFlag(QGraphicsItem.ItemIsMovable, False)
		self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)

		self.activated = False

	# Updates the item position if the game piece is being moved around
	def itemChange(self, change: 'QGraphicsItem.GraphicsItemChange', value: typing.Any) -> typing.Any:
		if (change == QGraphicsItem.ItemPositionChange):
			self.item_pos = value

		return super().itemChange(change, value)

	# Notifies the main window that the piece has been moved
	def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:

		self.pieceMoved.emit(self.ID, self.item_pos.x(), self.item_pos.y())

		return super().mouseReleaseEvent(event)


	# Updates the pieces position
	def movePiece(self, x = None, y = None):
		if x != None and y != None:
			self.x = x
			self.y = y

		self.setPos(self.x, self.y)

	
