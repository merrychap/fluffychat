import sys

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from PyQt5.Qt import QPushButton, QRect, QLabel, QToolTip, QFont


class GMainChat(QMainWindow):
    def __init__(self, *args):
        super().__init__(*args)

        self.init_ui()

    def init_ui(self):
        QToolTip.setFont(QFont('SansSerif', 10))

        self.statusBar().showMessage('Ready')

        self.create_widgets()

        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('Chat')
        self.show()

    def create_widgets(self):
        btn = QPushButton('Button', self)
        btn.setToolTip('This is <b>QPushButton</b> widget')
        btn.resize(btn.sizeHint())
        btn.move(50, 50)


def gmain():
    app = QApplication(sys.argv)

    form = GMainChat()
    form.show()

    sys.exit(app.exec_())
