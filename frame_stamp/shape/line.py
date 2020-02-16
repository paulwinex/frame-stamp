from __future__ import absolute_import
from .base_shape import BaseShape
from PIL import ImageDraw


class LineShape(BaseShape):
    """
    Линия

    Allowed parameters:
        x0
        x1
        y0
        y1
        width
    """
    shape_name = 'line'
    default_width = 2

    @property
    def x0(self):
        return self._eval_parameter('x0', default=0)

    @property
    def x1(self):
        return self._eval_parameter('x1', default=10)

    @property
    def y0(self):
        return self._eval_parameter('y0', default=0)

    @property
    def y1(self):
        return self._eval_parameter('y1', default=10)

    @property
    def x(self):
        return self.x0

    @property
    def y(self):
        return self.y0

    @property
    def x0_draw(self):
        return self.x0 + self.padding_left

    @property
    def y0_draw(self):
        return self.y0 + self.padding_top

    @property
    def x1_draw(self):
        return self.x1 - self.padding_right

    @property
    def y1_draw(self):
        return self.y1 - self.padding_bottom

    def render(self, size, **kwargs):
        canvas = self._get_canvas(size)
        img = ImageDraw.Draw(canvas)
        img.line((self.x_draw, self.y_draw, self.x1_draw, self.y1_draw), width=self.width, fill=self.color)
        return canvas
