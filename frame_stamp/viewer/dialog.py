from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import os, tempfile, traceback
from frame_stamp.viewer.canvas import Canvas
from frame_stamp.viewer.watch import TemplateFileWatch
from frame_stamp.utils import jsonc, open_file_location
from frame_stamp.stamp import FrameStamp
from pathlib import Path


class TemplateViewer(QMainWindow):
    state_file = Path('~/.template_viewer.json').expanduser()
    help_url = 'http://TODO'

    def __init__(self):
        super(TemplateViewer, self).__init__()
        self.setWindowTitle('Template Viewer')
        self.setAcceptDrops(True)

        # from py_console import console
        # self.c = console.Console(self)
        # self.c.show()

        self.template_file: Path = None
        self.template_name: str = None
        self.image = None
        self.tmp_file: str = None
        self.blank_image = None

        menubar = QMenuBar(self)
        file_mn = QMenu('File', menubar)
        menubar.addAction(file_mn.menuAction())
        view_mn = QMenu('View', menubar)
        menubar.addAction(view_mn.menuAction())
        help_mn = QMenu('Help', menubar)
        menubar.addAction(help_mn.menuAction())

        self.setMenuBar(menubar)

        file_mn.addAction(QAction('New Template...', file_mn, triggered=self.new_template))
        file_mn.addAction(QAction('Load Template...', file_mn, triggered=self.browse_template))
        file_mn.addAction(QAction('Open Current Template', file_mn, triggered=self.open_template))
        file_mn.addSeparator()
        file_mn.addAction(QAction('Load Background...', file_mn, triggered=self.browse_image))
        file_mn.addAction(QAction('Save Image As...', file_mn, triggered=self.save_image))
        file_mn.addSeparator()
        file_mn.addAction(QAction('Reset', file_mn, triggered=self.reset))
        file_mn.addAction(QAction('Exit', file_mn, triggered=self.close))

        view_mn.addAction(QAction('Actual Size', view_mn, triggered=self.actual_size))
        view_mn.addAction(QAction('Show Info', view_mn, triggered=self.show_info))
        self.fs = QAction('Full Screen', view_mn, triggered=self.set_full_screen)
        view_mn.addAction(self.fs)
        self.nfs = QAction('No Full Screen', view_mn, triggered=self.set_no_full_screen)
        view_mn.addAction(self.nfs)
        self.nfs.setShortcut(QKeySequence(Qt.Key_Escape))
        self.nfs.setVisible(False)
        help_mn.addAction(QAction('Documentation', view_mn, triggered=lambda: __import__('webbrowser').open(self.help_url)))

        self.dbg = QAction('Debug Shapes', view_mn, triggered=self.on_template_changed)
        self.dbg.setCheckable(True)
        view_mn.addAction(self.dbg)

        self.wd = QWidget(self)
        self.setCentralWidget(self.wd)
        self.ly = QVBoxLayout(self.wd)
        self.canvas = Canvas()
        self.ly.addWidget(self.canvas)
        self.err = QTextBrowser()
        self.ly.addWidget(self.err)
        self.err.hide()

        self.watcher = TemplateFileWatch()
        self.watcher.changed.connect(self.on_template_changed)
        self.status_line = QLabel()
        self.ly.addWidget(self.status_line)
        self.ly.setStretch(0, 1)
        self.ly.setStretch(1, 1)

        self.clear_timer = QTimer()
        self.clear_timer.timeout.connect(self.status_line.clear)
        self.clear_timer.setSingleShot(True)

        self.resize(800, 600)

    def set_error(self, text):
        self.err.setText(text)
        self.err.show()
        self.canvas.hide()

    def set_no_error(self):
        self.err.hide()
        self.canvas.show()

    def on_template_changed(self):
        QTimer.singleShot(100, self.update_image)

    def update_image(self, *args):
        self.set_no_error()
        try:
            img = self.render_template()
            self.canvas.set_image(img)
        except Exception as e:
            self.set_error(traceback.format_exc())

    def get_current_template(self) -> dict:
        if self.template_file and self.template_file.exists():
            templates = jsonc.load(self.template_file.open(encoding='utf-8'))
            try:
                template = self.get_template_from_data(templates, self.template_name)
            except Exception as e:
                QMessageBox.critical(self, 'Error', str(e))
                return
        else:
            template = None
        return template

    def render_template(self):
        template = self.get_current_template()
        image = self.image or self.get_dummy_image()
        viewer_variables = dict(
            # todo: custom variables from GUI
        )
        if template:
            variables = {**template.get('variables', {}), **viewer_variables}
            fs = FrameStamp(image, template, variables,
                            debug_shapes=self.dbg.isChecked())
            if not self.tmp_file:
                self.tmp_file = tempfile.mktemp(suffix='.png')
            fs.render(save_path=self.tmp_file)
            return self.tmp_file
        else:
            return image

    def get_dummy_image(self):
        p = QPixmap(1280, 720)
        p.fill(QColor('gray'))
        if not self.blank_image:
            self.blank_image = Path(tempfile.gettempdir(), 'stamp_blank.png').as_posix()
        p.save(self.blank_image, 'PNG')
        return self.blank_image

    def message(self, text, timeout=3):
        self.status_line.setText(str(text))
        if self.clear_timer.isActive():
            self.clear_timer.stop()
        self.clear_timer.start(timeout * 1000)

    def set_template_file(self, path: str, template_name: str = None):
        path = Path(path)
        if not path.exists():
            return
        self.template_file = path
        data: dict = jsonc.load(path.open())
        template = self.get_template_from_data(data, template_name)
        if not template:
            raise Exception('Template not set')

        self.template_file = path
        self.template_name = template['name']

        self.message('Set template: {} (Template name: {})'.format(self.template_file, self.template_name))
        self.watcher.set_file(self.template_file)
        self.update_image()

    def get_template_from_data(self, data, name=None) -> dict:
        if 'templates' in data:
            if len(data['templates']) > 1:
                if name:
                    for tmpl in data['templates']:
                        if tmpl['name'] == name:
                            return tmpl
                        else:
                            raise NameError(f'Template {name} not found')
                else:
                    dial = SelectTemplate([x['name'] for x in data['templates']])
                    if dial.exec_():
                        name = dial.list.selectedItems()[0].text()
                        return data[name]
                    else:
                        raise Exception('Canceled')
            else:
                return data['templates'][0]
        elif 'name' in data:
            return data
        else:
            raise RuntimeError('Wrong template format')

    def set_image(self, path: str):
        self.image = str(path)
        self.message('Set Image: {}'.format(path))
        self.update_image()
        sz = QImage(path).size()
        self.message('Image loaded: {}x{}'.format(sz.width(), sz.height()), timeout=10)

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
        self.set_no_error()
        if Path(path).suffix == '.json':
            self.set_template_file(path)
            return True
        elif Path(path).suffix in ['.jpg', '.png']:
            self.set_image(path)
            return True

    def reset(self):
        self.template_name = None
        self.template_file = None
        self.image = None
        self.on_template_changed()

    def new_template(self):
        from frame_stamp.viewer.default_template import default_template
        path, _ = QFileDialog.getSaveFileName(self, 'New Template', os.path.expanduser('~'))
        if path:
            norm_path = Path(path).with_suffix('.json')
            jsonc.dump(default_template, norm_path.open('w'), indent=2)
            self.set_template_file(norm_path)
            open_file_location(norm_path)

    def open_template(self):
        if self.template_file.exists():
            open_file_location(self.template_file)
        else:
            self.message('Template not set')

    def browse_image(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Select Image', os.path.expanduser('~'), filter='Images (*.png *.jpg)')
        if path:
            self.set_image(path)

    def browse_template(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Select Template', os.path.expanduser('~'), filter='JSON (*.json)')
        if path:
            self.set_template_file(path)

    def save_image(self):
        if not self.canvas:
            self.message('Error: Image not exists')
            return
        if not self.canvas.path or not os.path.exists(self.canvas.path):
            self.message('Error: Image not rendered yet')
            return
        path, _ = QFileDialog.getSaveFileName(self, 'Save Image', os.path.expanduser('~'), filter='PNG (*.png)')
        if path:
            if not path.endswith('.png'):
                path = path+'.png'
            import shutil
            shutil.copyfile(self.canvas.path, path)

    def actual_size(self):
        if self.image:
            size = QPixmap(str(self.image)).size()
            self.resize(size+QSize(100, 100))

    def set_full_screen(self):
        self.showFullScreen()
        self.fs.setVisible(False)
        self.nfs.setVisible(True)

    def set_no_full_screen(self):
        self.showNormal()
        self.fs.setVisible(True)
        self.nfs.setVisible(False)

    def closeEvent(self, event):
        self.save_state()
        super(TemplateViewer, self).closeEvent(event)

    def showEvent(self, event):
        self.load_state()
        super(TemplateViewer, self).showEvent(event)

    def save_state(self):
        data = {}
        if self.state_file.exists():
            try:
                data = jsonc.load(self.state_file.open())
            except Exception as e:
                print(e)
        data['image'] = str(self.image)
        data['template_file'] = self.template_file.as_posix() if self.template_file else None
        data['template_name'] = self.template_name
        data['fullscreen'] = self.isFullScreen()

        if not data['fullscreen']:
            data['pos'] = [self.pos().x(), self.pos().y()]
            data['size'] = [self.size().width(), self.size().height()]
        jsonc.dump(data, self.state_file.open('w'), indent=2)

    def load_state(self):
        if os.path.exists(self.state_file):
            try:
                data = jsonc.load(open(self.state_file))    # type: dict
            except:
                return
            if data.get('pos'):
                self.move(*data['pos'])
            if data.get('size'):
                self.resize(*data['size'])
            img = data.get('image')
            if img and os.path.exists(img):
                self.set_image(img)
            tmpl = data.get('template_file')
            if tmpl:
                self.set_template_file(tmpl, data.get('template_name'))
            if data.get('fullscreen'):
                self.set_full_screen()

    def show_info(self):
        dial = QMessageBox(self)
        dial.setWindowTitle('Viewer info')
        sz = QImage(str(self.image)).size()
        dial.setText('<b>Template File:</b><br>  {}<br><br>'
                     '<b>Template Name:</b><br>  {}<br><br>'
                     '<b>Image File:</b><br> {}<br><br>'
                     '<b>Image Size:</b><br>  {}x{}<br><br>'.format(
            self.template_file,
            self.template_name,
            self.image,
            sz.width(), sz.height()

        ))
        dial.exec_()


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

def main():
    app = QApplication([])
    v = TemplateViewer()
    v.show()
    app.exec()


if __name__ == '__main__':
    main()
