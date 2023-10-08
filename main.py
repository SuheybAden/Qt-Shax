from PyQt5 import QtWidgets
from ui.main_window import MainWindow
import sys


def main():
    app = QtWidgets.QApplication([])
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
