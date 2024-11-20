from .base_shape import BaseShape
from PIL import ImageDraw
from frame_stamp.utils import cached_result
from ..utils.point import Point, PointInt
from ..utils.rect import Rect


class RectShape(BaseShape):
    """
    Прямоугольник

    Allowed parameters:
        border_width    : толщина обводки
        border_color    : цвет обводки
    """
    shape_name = 'rect'

    default_height = 100
    default_width = 100

    @property
    @cached_result
    def border(self):
        value = self._eval_parameter('border', default=None)
        if value is None:
            return None
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

    def shape_canvas_offset(self):
        return self.border_width

    def draw_shape(self, shape_canvas, canvas_size, center, zero_point, **kwargs):
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


