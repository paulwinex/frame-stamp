import tempfile

from PySide6.QtCore import *
from PySide6.QtWidgets import *


class TemplateFileWatch(QObject):
    changed = Signal(str)

    def __init__(self):
        super(TemplateFileWatch, self).__init__()
        self.fsw = QFileSystemWatcher()
        self.fsw.fileChanged.connect(self.changed)

    def set_file(self, path):
        if self.fsw.files():
            self.fsw.removePaths(self.fsw.files())
        self.fsw.addPath(str(path))


if __name__ == '__main__':

    def callback(path):
        print('Changed', path)

    app = QApplication([])
    w = TemplateFileWatch()
    file = tempfile.mktemp()
    with open(file, 'w') as f:
        f.write('test')
    w.set_file(file)
    w.changed.connect(callback)
    print('Try to change file', file)
    app.exec_()
