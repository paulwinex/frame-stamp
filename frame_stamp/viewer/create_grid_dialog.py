import tempfile
from pathlib import Path

from PySide6.QtWidgets import *
from PySide6.QtCore import *


class CreateGridDialog(QDialog):
    default_size = [1280, 720]

    def __init__(self, *args):
        super().__init__(*args)
        self.setWindowFlags(Qt.Tool)
        self.setWindowTitle("Create Grid")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Image Size:"))
        h_layout = QHBoxLayout()
        self.width_input = QSpinBox(self, maximum=4096, minimum=320)
        h_layout.addWidget(self.width_input)
        self.height_input = QSpinBox(self, maximum=4096, minimum=240)
        h_layout.addWidget(self.height_input)
        layout.addLayout(h_layout)
        layout.addWidget(QPushButton("Create", clicked=self.accept))
        self.resize(300, 10)

        self.path = None
        self.width_input.setValue(self.default_size[0])
        self.height_input.setValue(self.default_size[1])

    def accept(self):
        from frame_stamp.utils.background_grig import create_grid_image

        self.path = create_grid_image(Path(tempfile.gettempdir(), "pixel_grid.png").as_posix(), [self.width_input.value(), self.height_input.value()])
        return super().accept()


if __name__ == '__main__':
    app = QApplication()
    dialog = CreateGridDialog()
    dialog.exec()