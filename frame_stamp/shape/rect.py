from __future__ import absolute_import
from .base_shape import BaseShape


class RectShape(BaseShape):
    """
    Прямоугольник

    Allowed parameters:
        x
        y
        width
        hight
        color

    """
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
    def x0(self):
        return self.x

    @property
    def x1(self):
        return self.x0 + self.width

    @property
    def y0(self):
        return self.y

    @property
    def y1(self):
        return self.y0 + self.height

    @property
    def width(self):
        return self._eval_parameter('width')

    @property
    def height(self):
        return self._eval_parameter('hight')

    @property
    def center(self):
        return (
            (self.x0+self.x1)/2,
            (self.y0+self.y1)/2
        )

    @property
    def bound(self):
        return self.x0, self.y0, self.y0, self.y1

    def render(self, img, **kwargs):
        img.rectangle([(self.x0, self.y0), (self.x1, self.y1)], self.color)

