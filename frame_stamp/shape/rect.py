from .base_shape import BaseShape


class RectShape(BaseShape):
    """
    Прямоугольник

    Allowed parameters:
        x
        y
        width
        hight
        color
        border_color
        border_width

    """
    shape_name = 'rect'

    @property
    def top(self):
        return self.y0

    @property
    def left(self):
        return self.x0

    @property
    def bottom(self):
        return self.y1

    @property
    def right(self):
        return self.x1

    @property
    def x0(self):
        return self.x

    @property
    def x1(self):
        return self.x0 + self.width

    @property
    def y0(self):
        return self.y

    @property
    def y1(self):
        return self.y0 + self.height

    @property
    def width(self):
        return self._eval_parameter('width')

    @property
    def height(self):
        return self._eval_parameter('hight')

    @property
    def center(self):
        return (
            (self.x0+self.x1)/2,
            (self.y0+self.y1)/2
        )

    @property
    def font_size(self) -> int:
        size = self._eval_parameter('font_size')    # type: int
        if size == 0:
            raise ValueError('Font size can`t be zero. Shape "{}"'.format(self))
        return size

    @property
    def bound(self):
        return self.x0, self.y0, self.y0, self.y1

    @property
    def border_width(self):
        return self._eval_parameter('border_width', default=0)

    @property
    def border_color(self):
        return self._eval_parameter('border_color', default='black')

    def render(self, img, **kwargs):
        img.rectangle([(self.x0, self.y0), (self.x1, self.y1)], self.color)
        border = self.border_width
        if border:
            # img.rectangle([(self.x0, self.y0), (self.x1, self.y1)], outline='red')
            points = [
                (self.left, self.top),
                (self.right, self.top),
                (self.right, self.bottom),
                (self.left, self.bottom),
                (self.left, self.top)
            ]
            img.line(points, self.border_color, self.border_width)


class Cell(object):
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
