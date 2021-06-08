from __future__ import absolute_import
from .base_shape import BaseShape
from PIL import ImageDraw
from frame_stamp.utils import cached_result


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
    def x(self):
        pts = self.points
        if pts:
            _x = min([x[0] for x in pts])
        else:
            _x = 0
        return _x + self.parent.x

    @property
    @cached_result
    def y(self):
        pts = self.points
        if pts:
            _y = min([x[1] for x in pts])
        else:
            _y = 0
        return _y + self.parent.y

    @property
    @cached_result
    def width(self):
        pts = self.points
        if pts:
            w = max([x[0] for x in pts])
        else:
            w = 0
        return w + self.parent.x - self.x

    @property
    @cached_result
    def height(self):
        pts = self.points
        if pts:
            h = max([x[1] for x in pts])
        else:
            h = 0
        return h + self.parent.y - self.y

    def draw_shape(self, size, **kwargs):
        canvas = self._get_canvas(size)
        pts = self.points
        if pts:
            pts = tuple(tuple([self._eval_parameter_convert('', c) for c in x]) for x in pts)
            img = ImageDraw.Draw(canvas)
            img.line(pts, width=self.thickness, fill=self.color)
            if self.joints:
                for (x, y) in pts:
                    img.ellipse(((x - self.thickness/2)+1, (y - self.thickness/2)+1,
                                 (x + self.thickness/2)-1, (y + self.thickness/2)-1), fill=self.color)
        return canvas
