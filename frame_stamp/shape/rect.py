from .base_shape import BaseShape


class RectShape(BaseShape):
    """
    Прямоугольник

    Allowed parameters:
        border_width    : толщина обводки
        border_color    : цвет обводки
    """
    shape_name = 'rect'

    @property
    def border_width(self):
        return self._eval_parameter('border_width', default=0)

    @property
    def border_color(self):
        return self._eval_parameter('border_color', default='black')

    def render(self, img, **kwargs):
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

