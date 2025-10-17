from PySide6.QtWidgets import QApplication
import sys

from gui.qt_main_window import QtMainWindow


def main():
    app = QApplication(sys.argv)
    win = QtMainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()



