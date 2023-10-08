from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtCore import pyqtSlot, QVariant
import os

class SettingsWindow(QtWidgets.QDialog):
	def __init__(self, settings) -> None:
		super().__init__()
		self.load_ui()

		self.settings = settings
		self.readSettings()

	# Loads the Qt UI file with the same name
	def load_ui(self):
		cwd = os.getcwd()
		filename = os.path.splitext(os.path.basename(__file__))[0]
		uic.loadUi(cwd + "/ui_files/" + filename + ".ui", self)
		self.connect_all()

    # Connects all the signals and slots
	def connect_all(self):
		self.buttonBox.accepted.connect(self.writeSettings)

	# Saves the user's settings before closing window
	@pyqtSlot()
	def writeSettings(self):
		self.settings.setValue("mode", self.modeComboBox.currentText())
		self.settings.setValue("url", self.urlLineEdit.text())
		self.settings.setValue("minPieces", self.minPiecesSpinBox.value())
		self.settings.setValue("maxPieces", self.maxPiecesSpinBox.value())

	# Loads the current settings into the UI
	def readSettings(self):
		self.modeComboBox.setCurrentText(self.settings.value("mode", "Local"))
		self.urlLineEdit.setText(self.settings.value("url", "ws://192.168.0.21:8765"))
		self.minPiecesSpinBox.setValue(int(self.settings.value("minPieces", 2)))
		self.maxPiecesSpinBox.setValue(int(self.settings.value("maxPieces", 10)))
		