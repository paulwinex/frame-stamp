from __future__ import absolute_import
from .base_shape import BaseShape


class RectShape(BaseShape):
    shape_name = 'rect'

    def top(self, absolute=False):
        pass

    def left(self, absolute=False):
        pass

    def bottom(self, absolute=False):
        pass

    def right(self, absolute=False):
        pass

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
        return

    @property
    def y0(self):
        return self._eval_parameter('y')

    @property
    def y1(self):
        return

    def width(self):
        return self._eval_parameter('width')

    def height(self):
        return self._eval_parameter('hight')

    def center(self, absolute=False):
        pass

    @property
    def color(self):
        return 'red'

    def render(self, painter, **kwargs):
        return painter.rectangle([self.x0, self.y0, self.x1, self.y1], self.color)
