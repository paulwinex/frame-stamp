from typing import Union

from PIL import ImageDraw, Image

from frame_stamp.utils import cached_result
from frame_stamp.utils.point import PointInt, Point
from frame_stamp.utils.rect import Rect
from .base_shape import BaseShape


class RectShape(BaseShape):
    """
    Rectangle shape

    Allowed parameters:
        border_width    : толщина обводки
        border_color    : цвет обводки
    """
    shape_name = 'rect'

    default_height = 100
    default_width = 100

    @property
    @cached_result
    def border(self) -> dict:
        value = self._eval_parameter('border', default=None)
        if value is None:
            return None
        assert isinstance(value, dict), 'Border value must be a dict'
        value.setdefault('width', self.border_width)
        value.setdefault('color', self.border_color)
        return value

    @property
    @cached_result
    def border_width(self) -> int:
        return self._eval_parameter('border_width', default=0)

    @property
    @cached_result
    def border_color(self) -> Union[tuple[int, int, int], str]:
        return self._eval_parameter('border_color', default='black')

    def shape_canvas_offset(self) -> int:
        return self.border_width

    def draw_shape(self, shape_canvas: Image.Image, canvas_size: tuple[int, int], center: Point, zero_point: Point, **kwargs):
        img = ImageDraw.Draw(shape_canvas)
        point1 = zero_point+PointInt(self.width, self.height)
        img.rectangle((
             (*zero_point,), (*point1,)),
            self.color)
        border = self.border
        rect = Rect(zero_point.x, zero_point.y, self.width, self.height)
        if border and border.get('width'):
            points = [
                (rect.left, rect.top),
                (rect.right, rect.top),
                (rect.right, rect.bottom),
                (rect.left, rect.bottom),
                (rect.left, rect.top)
            ]
            img.line(points, self.border['color'], self.border['width'])


