from PyQt5 import QtWidgets, uic, QtGui
import os

class MainWindow(QtWidgets.QMainWindow):
	def __init__(self) -> None:
		super().__init__()
		self.load_ui()

	def load_ui(self):
		cwd = os.getcwd()
		filename = os.path.splitext(os.path.basename(__file__))[0]
		uic.loadUi(cwd + "/ui_files/" + filename + ".ui", self)
		self.connect_all()

    # Connects all the signals and slots
	def connect_all(self):
		pass