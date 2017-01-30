import sys

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from PyQt5.Qt import QPushButton, QRect, QLabel


class GUIMain(QMainWindow):
    def __init__(self, *args):
        QMainWindow.__init__(self, *args)
        self.cw = QWidget(self)
        self.setCentralWidget(self.cw)

    def init_form(self):
        self.btn = QPushButton('Click pls', self.cw)
        self.btn1setGeometry(QRect(50, 50, 100, 30))

        self.label = QLabel('No commands running', self.cw)
        self.btn.clicked.connect(self.btn, self.make_action)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = GUIMain()
    form.show()
    sys.exit(app.exec_())
