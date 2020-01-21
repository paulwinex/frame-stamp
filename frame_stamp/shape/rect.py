from __future__ import absolute_import
from .base_shape import BaseShape


class RectShape(BaseShape):
    shape_name = 'rect'

    @property
    def top(self):
        return self.y0

    @property
    def left(self):
        return self.x0

    @property
    def bottom(self):
        return self.y1

    def right(self):
        return self.x1

    @property
    def x(self):
        return self.x0

    @property
    def y(self):
        return self.y0

    @property
    def x0(self):
        return self._eval_parameter('x')

    @property
    def x1(self):
        return self.x0+self.width

    @property
    def y0(self):
        return self._eval_parameter('y')

    @property
    def y1(self):
        return self.y0+self.height

    @property
    def width(self):
        return self._eval_parameter('width')

    @property
    def height(self):
        return self._eval_parameter('hight')

    @property
    def center(self):
        return

    def render(self, img, **kwargs):
        img.rectangle([(self.x0, self.y0), (self.x1, self.y1)], self.color)

    def text_line(self, line_num):
        text_size = self.defaults.get('text_size', 14)
        pass
