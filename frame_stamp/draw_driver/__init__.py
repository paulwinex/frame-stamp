
class AbstractDrawEngine(object):

    def __init__(self, input_file, output_path, shapes, **kwargs):
        self._input_file = input_file
        self._output_path = output_path
        self.shapes = shapes

    def draw_rect(self, x, y, w, h, fill, border=None):
        pass

    def draw_elipse(self, x, y, w, h, fill, border=None):
        pass

    def draw_text(self, x, y, text, size, color='black', opacity=1.0):
        pass

    def draw_line(self, x1, y1, x2, y2, color, width=1):
        pass

    def draw_image(self, x, y, w, h, path, opacity=1.0, resize='crop'):
        pass

    def draw_point(self, x, y, color, opacity=1.0):
        pass

    def draw_polygon(self, points, closed=True, fill=None, border=None):
        pass
