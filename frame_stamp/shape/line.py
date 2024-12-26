from __future__ import absolute_import
from .base_shape import BaseShape
from PIL import ImageDraw
from frame_stamp.utils import cached_result
from ..utils.point import Point, PointInt


class LineShape(BaseShape):
    """
    Линия

    Allowed parameters:
        points
        thickness
        joints
    """
    shape_name = 'line'
    default_width = 2

    @property
    @cached_result
    def points(self):
        return self._eval_parameter('points', default=[])

    @property
    @cached_result
    def thickness(self):
        return int(self._eval_parameter('thickness', default=self.default_width))

    @property
    @cached_result
    def joints(self):
        return self._eval_parameter('joints', default=True)

    @property
    @cached_result
    def width(self):
        pts = self.points
        if pts:
            max_x = max([x[0] for x in pts])
            w = max_x
        else:
            w = 0
        return w

    @property
    @cached_result
    def height(self):
        pts = self.points
        if pts:
            max_y = max([x[1] for x in pts])
            h = max_y
        else:
            h = 0
        return h

    def draw_shape(self, shape_canvas, canvas_size, center, zero_point: Point, **kwargs):
        pts = self.points
        if pts:
            pts = tuple(tuple([self._eval_parameter_convert('', c) for c in x]) for x in pts)
            pts = [(Point(*pt) + zero_point).tuple for pt in pts]
            img = ImageDraw.Draw(shape_canvas)
            img.line(pts, width=self.thickness, fill=self.color)
            if self.joints:
                for (x, y) in pts:
                    img.ellipse(((x - self.thickness / 2) + 1, (y - self.thickness / 2) + 1,
                                 (x + self.thickness / 2) - 1, (y + self.thickness / 2) - 1), fill=self.color)
