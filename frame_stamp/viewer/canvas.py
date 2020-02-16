from Qt.QtWidgets import *
from Qt.QtCore import *
from Qt.QtGui import *


class Canvas(QWidget):
    def __init__(self):
        super(Canvas, self).__init__()
        self.image = None

    def set_image(self, path):
        pix = QPixmap(path)
        self.image = pix
        self.repaint()

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.fillRect(event.rect(), QColor('black'))
        if self.image:
            size = QSize(
                min([self.image.width(), event.rect().width()]),
                min([self.image.height(), event.rect().height()]),
            )
            pix = self.image.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(
                (event.rect().width() - pix.width()) // 2,
                (event.rect().height() - pix.height()) // 2,
                pix)
        painter.end()
