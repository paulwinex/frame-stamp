from Qt.QtWidgets import *
from Qt.QtCore import *
from frame_stamp.viewer.canvas import Canvas
from frame_stamp.viewer.watch import TemplateFileWatch
import os
from cgf_tools import jsonc
from frame_stamp.stamp import FrameStamp


class TemplateViewer(QWidget):
    def __init__(self):
        super(TemplateViewer, self).__init__()
        self.setWindowTitle('Template Viewer')
        self.setAcceptDrops(True)

        self.template_file = None
        self.template_name = None
        self.image = None

        self.ly = QVBoxLayout(self)
        self.canvas = Canvas()
        self.ly.addWidget(self.canvas)
        self.watcher = TemplateFileWatch()
        self.watcher.changed.connect(self.update_image)
        self.status_line = QLabel()
        self.ly.addWidget(self.status_line)
        self.ly.setStretch(0, 1)
        self.resize(800, 600)

    def update_image(self, *args):
        print('UPDATE IMAGE')

    def render_template(self):
        template = json
        fs = FrameStamp(file_inp, preset_slate, variables, debug_shapes=True)
        out = fs.render(save_path=file_out)

    def message(self, text):
        self.status_line.setText(str(text))
        QTimer.singleShot(3000, self.status_line.clear)

    def set_template_file(self, path):
        self.template_file = path
        data = jsonc.load(open(path))
        templates = data['templates']
        if not templates:
            return
        if len(templates) > 1:
            dial = SelectTemplate([x['name'] for x in templates])
            if dial.exec_():
                name = dial.list.selectedItems()[0].text()
                self.template_file = path
                self.template_name = name
            else:
                return
        else:
            self.template_file = path
            self.template_name = templates[0]['name']
        self.message('Set template: {} ({})'.format(self.template_file, self.template_name))
        self.watcher.set_file(self.template_file)
        self.update_image()

    def set_image(self, path):
        self.image = path
        self.message('Set Image: {}'.format(path))

    def dropEvent(self, event, *args, **kwargs):
        mimedata = event.mimeData()
        if mimedata.hasUrls():
            for f in mimedata.urls():
                if self.on_file_dropped(f.toLocalFile()):
                    break
        QApplication.restoreOverrideCursor()

    def dragEnterEvent(self, event):
        if event.source() is self:
            event.ignore()
        else:
            mimedata = event.mimeData()
            if mimedata.hasUrls():
                event.accept()
            else:
                event.ignore()

    def dragMoveEvent(self, event):
        if event.source() is self:
            event.ignore()
        else:
            mimedata = event.mimeData()
            if mimedata.hasUrls():
                event.accept()
            else:
                event.ignore()

    def on_file_dropped(self, path):
        if os.path.splitext(path)[-1] == '.json':
            try:
                data = jsonc.load(open(path))
            except:
                print('File load error: {}'.format(path))
                return
            templates = data.get('templates')
            if not templates:
                print('No templates in file: {}'.format(path))
                return
            else:
                self.set_template_file(path)
                return True
        elif os.path.splitext(path)[-1] in ['.jpg', '.png']:
            self.set_image(path)
            return True


class SelectTemplate(QDialog):
    def __init__(self, names):
        super(SelectTemplate, self).__init__()
        self.setWindowTitle('Select Template')
        self.ly = QVBoxLayout(self)
        self.list = QListWidget()
        self.ly.addWidget(self.list)
        self.list.addItems(names)
        self.btn = QPushButton('Select', clicked=self.on_click)
        self.ly.addWidget(self.btn)

    def on_click(self):
        if self.list.selectedItems():
            self.accept()


if __name__ == '__main__':
    app = QApplication([])
    v = TemplateViewer()
    v.show()
    app.exec_()
