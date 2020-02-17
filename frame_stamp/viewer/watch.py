from Qt.QtCore import *
from Qt.QtWidgets import *


class TemplateFileWatch(QObject):
    changed = Signal(str)

    def __init__(self):
        super(TemplateFileWatch, self).__init__()
        self.fsw = QFileSystemWatcher()
        self.fsw.fileChanged.connect(self.changed)

    def set_file(self, path):
        if self.fsw.files():
            self.fsw.removePaths(self.fsw.files())
        self.fsw.addPath(path)


if __name__ == '__main__':

    def callback(path):
        print('Changed', path)

    app = QApplication([])
    w = TemplateFileWatch()
    w.set_file('/home/paul/dev/frame_stamp/_tmp/qyest.py')
    w.changed.connect(callback)
    app.exec_()
