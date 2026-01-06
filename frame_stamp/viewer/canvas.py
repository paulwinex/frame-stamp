from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


class Canvas(QWidget):
    def __init__(self):
        super(Canvas, self).__init__()
        self.image = None
        self.path = None

    def set_image(self, path: str):
        self.path = path
        pix = QPixmap(path)
        self.image = pix
        self.repaint()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(event.rect(), QColor('#646565'))
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
