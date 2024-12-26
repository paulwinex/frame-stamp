from __future__ import absolute_import

from . import LineShape
from PIL import ImageDraw
from frame_stamp.utils import cached_result
from ..utils.point import Point, PointInt


class PolygonShape(LineShape):
    """
    Polygon

    Allowed parameters:
        points
        thickness
        joints
        color
    """
    shape_name = 'polygon'
    default_width = 2

    @property
    @cached_result
    def points(self):
        return self._eval_parameter('points', default=[])

    @property
    @cached_result
    def border(self):
        value = self._eval_parameter('border', default=None)
        if value is None:
            value = {}
        assert isinstance(value, dict), 'Border value must be a dict'
        value.setdefault('width', self.border_width)
        value.setdefault('color', self.border_color)
        return value

    @property
    @cached_result
    def border_width(self):
        return self._eval_parameter('border_width', default=0)

    @property
    @cached_result
    def border_color(self):
        return self._eval_parameter('border_color', default='black')

    @property
    @cached_result
    def joints(self):
        return self._eval_parameter('joints', default=True)

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
            draw_kwargs = {}
            if self.border:
                draw_kwargs['outline'] = self.border['color']
                draw_kwargs['width'] = self.border['width']
            img.polygon(pts, fill=self.color, **draw_kwargs)
            if self.joints:
                for (x, y) in pts:
                    img.ellipse(((x - self.border['width'] / 2) + 1, (y - self.border['width'] / 2) + 1,
                                 (x + self.border['width'] / 2) - 1, (y + self.border['width'] / 2) - 1), fill=self.border['color'])
