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
    def border_width(self):
        return self._eval_parameter('border_width', default=0)

    @property
    @cached_result
    def border_color(self):
        return self._eval_parameter('border_color', default='black')

    # def draw_shape(self, size, **kwargs):
    #     overlay = self._get_canvas(size)
    #     img = ImageDraw.Draw(overlay)
    #     img.rectangle(
    #         ((self.x_draw, self.y_draw),
    #          (self.width_draw, self.height_draw)),
    #         self.color)
    #     border = self.border_width
    #     if border:
    #         points = [
    #             (self.left, self.top),
    #             (self.right, self.top),
    #             (self.right, self.bottom),
    #             (self.left, self.bottom),
    #             (self.left, self.top)
    #         ]
    #         img.line(points, self.border_color, self.border_width)
    #     return overlay

    def shape_canvas_offset(self):
        return self.border_width

    def draw_shape(self, shape_canvas, canvas_size, center, zero_point, **kwargs):
        img = ImageDraw.Draw(shape_canvas)
        point1 = zero_point+PointInt(self.width, self.height)
        img.rectangle((
             (*zero_point,), (*point1,)),
            self.color)
        border = self.border_width
        rect = Rect(zero_point.x, zero_point.y, self.width, self.height)
        if border:
            points = [
                (rect.left, rect.top),
                (rect.right, rect.top),
                (rect.right, rect.bottom),
                (rect.left, rect.bottom),
                (rect.left, rect.top)
            ]
            img.line(points, self.border_color, self.border_width)


