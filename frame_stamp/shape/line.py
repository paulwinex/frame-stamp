from __future__ import absolute_import
from .base_shape import BaseShape


class LineShape(BaseShape):
    """
    Линия

    Allowed parameters:
        x1
        x2
        y1
        y2
        width
        color
    """
    shape_name = 'line'

    @property
    def width(self):
        return

    @property
    def color(self):
        return
