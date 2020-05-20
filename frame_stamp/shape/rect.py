from .base_shape import BaseShape
from PIL import ImageDraw
from frame_stamp.utils import cached_result


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

    def draw_shape(self, size, **kwargs):
        overlay = self._get_canvas(size)
        img = ImageDraw.Draw(overlay)
        img.rectangle(
            ((self.x_draw, self.y_draw),
             (self.width_draw, self.height_draw)),
            self.color)
        border = self.border_width
        if border:
            points = [
                (self.left, self.top),
                (self.right, self.top),
                (self.right, self.bottom),
                (self.left, self.bottom),
                (self.left, self.top)
            ]
            img.line(points, self.border_color, self.border_width)
        return overlay

