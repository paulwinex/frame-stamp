from __future__ import absolute_import

from typing import Union

from PIL import ImageDraw, Image

from frame_stamp.shape.base_shape import BaseShape
from frame_stamp.utils import cached_result
from frame_stamp.utils.point import Point


class LineShape(BaseShape):
    """
    Simple line shape.

    Allowed parameters:
        points
        thickness
        joints
    """
    shape_name = 'line'
    default_width = 2

    @property
    @cached_result
    def points(self) -> list[list]:
        return self._eval_parameter('points', default=[])

    @property
    @cached_result
    def thickness(self) -> Union[int, float]:
        return int(self._eval_parameter('thickness', default=self.default_width))

    @property
    @cached_result
    def joints(self) -> bool:
        return self._eval_parameter('joints', default=True)

    @property
    @cached_result
    def width(self) -> int:
        pts = self.points
        if pts:
            max_x = max([x[0] for x in pts])
            w = max_x
        else:
            w = 0
        return w

    @property
    @cached_result
    def height(self) -> int:
        pts = self.points
        if pts:
            max_y = max([x[1] for x in pts])
            h = max_y
        else:
            h = 0
        return h

    def draw_shape(
            self, shape_canvas: Image.Image, canvas_size: tuple[int, int], center: Point, zero_point: Point, **kwargs
        ) -> None:
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
