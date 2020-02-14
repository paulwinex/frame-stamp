from __future__ import absolute_import
from .base_shape import BaseShape


class LineShape(BaseShape):
    """
    Линия

    Allowed parameters:
        x0
        x1
        y0
        y1
        width
    """
    shape_name = 'line'

    @property
    def width(self):
        return

    @property
    def color(self):
        return
