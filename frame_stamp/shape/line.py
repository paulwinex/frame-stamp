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

    def _render_debug(self, default_render, size):
        return default_render

    @property
    def x0(self):
        raise AttributeError

    @property
    def x1(self):
        raise AttributeError

    @property
    def y0(self):
        raise AttributeError

    @property
    def y1(self):
        raise AttributeError

    @property
    def padding(self):
        raise AttributeError

    @property
    def padding_top(self):
        raise AttributeError

    @property
    def padding_left(self):
        raise AttributeError

    @property
    def padding_bottom(self):
        raise AttributeError

    @property
    def padding_right(self):
        raise AttributeError

    @property
    def points(self):
        return self._eval_parameter('points', default=[])

    @property
    def thickness(self):
        return self._eval_parameter('thickness', default=self.default_width)

    @property
    def x(self):
        pts = self.points
        if pts:
            return min([x[0] for x in pts])
        else:
            return 0

    @property
    def y(self):
        pts = self.points
        if pts:
            return min([x[1] for x in pts])
        else:
            return 0

    @property
    def width(self):
        pts = self.points
        if pts:
            return max([x[0] for x in pts])
        else:
            return 0

    @property
    def height(self):
        pts = self.points
        if pts:
            return max([x[1] for x in pts])
        else:
            return 0

    def draw_shape(self, size, **kwargs):
        canvas = self._get_canvas(size)
        pts = self.points
        if pts:
            pts = tuple(tuple([self._eval_parameter_convert('', c) for c in x]) for x in pts)
            img = ImageDraw.Draw(canvas)
            img.line(pts, width=self.thickness, fill=self.color)
        return canvas
