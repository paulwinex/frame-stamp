from .base_shape import BaseShape
from PIL import ImageDraw
from frame_stamp.utils import cached_result
from ..utils.point import PointInt


class CircleShape(BaseShape):
    """
    Circle shape

    """
    shape_name = 'circle'

    default_darius = 50

    @property
    @cached_result
    def radius(self):
        return self._eval_parameter('radius', default=self.default_darius)

    @property
    def width(self):
        return self.radius * 2

    @property
    def height(self):
        return self.radius*2

    @property
    @cached_result
    def outline(self):
        value = self._eval_parameter('outline', default=None)
        if value is None:
            return None
        if isinstance(value, (int, float)):
            value = {'width': value}
        assert isinstance(value, dict), 'Outline value must be a dict'
        value.setdefault('width', self.outline_width)
        value.setdefault('color', self.outline_color)
        return value

    @property
    @cached_result
    def outline_width(self):
        return self._eval_parameter('outline_width', default=0)

    @property
    @cached_result
    def outline_color(self):
        return self._eval_parameter('outline_color', default='black')

    def shape_canvas_offset(self):
        return self.outline_width

    def draw_shape(self, shape_canvas, canvas_size, center, zero_point, **kwargs):
        img = ImageDraw.Draw(shape_canvas)
        point1 = zero_point+PointInt(self.width, self.height)
        kwargs = {}
        if self.outline:
            kwargs['outline'] = self.outline['color']
            kwargs['width'] = self.outline['width']
        img.ellipse((
             (*zero_point, *point1,)
        ),
            fill=self.color,
            **kwargs
        )

