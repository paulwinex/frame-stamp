from __future__ import annotations
import math


class Point:
    def __init__(self, x, y=None):
        if isinstance(x, (list, tuple)):
            assert len(x) == 2, 'Point must have two coordinates'
            x, y = x
        elif isinstance(x, Point):
            x, y = x.x, x.y
        elif isinstance(x, (int, float)) and y is None:
            raise ValueError('Point must have two coordinates')
        assert isinstance(y, (int, float)), 'Y coordinate must be int or float'
        self._x = x
        self._y = y

    def __add__(self, other):
        if isinstance(other, Point):
            return Point(self._x + other.x, self._y + other.y)
        elif isinstance(other, (int, float)):
            return Point(self._x + other, self._y + other)
        else:
            raise TypeError(f"Unsupported operand type(s) for +: 'Point' and '{type(other)}'")

    def __sub__(self, other):
        if isinstance(other, Point):
            return Point(self._x - other.x, self._y - other.y)
        elif isinstance(other, (int, float)):
            return Point(self._x - other, self._y - other)
        else:
            raise TypeError(f"Unsupported operand type(s) for -: 'Point' and '{type(other)}'")

    def __iter__(self):
        """
        For supporting:
            coords = [*point]
        :return:
        """
        yield self._x
        yield self._y

    def __mul__(self, value):
        if isinstance(value, Point):
            return Point(self._x * value.x, self._y * value.y)
        elif isinstance(value, (int, float)):
            return Point(self._x * value, self._y * value)
        else:
            raise TypeError(f"Unsupported operand type(s) for *: 'Point' and '{type(value)}'")

    def __truediv__(self, other):
        if isinstance(other, Point):
            return Point(self._x / other.x, self._y / other.y)
        elif isinstance(other, (int, float)):
            return Point(self._x / other, self._y / other)
        else:
            raise TypeError(f"Unsupported operand type(s) for /: 'Point' and '{type(other)}'")

    def __floordiv__(self, other):
        if isinstance(other, Point):
            return Point(self._x // other.x, self._y // other.y)
        elif isinstance(other, (int, float)):
            return Point(self._x // other, self._y // other)
        else:
            raise TypeError(f"Unsupported operand type(s) for //: 'Point' and '{type(other)}'")

    def __divmod__(self, other):
        if isinstance(other, Point):
            return Point(self._x / other.x, self._y / other.y)
        elif isinstance(other, (int, float)):
            return Point(self._x / other, self._y / other)
        else:
            raise TypeError(f"Unsupported operand type(s) for /: 'Point' and '{type(other)}'")

    def __eq__(self, other: 'Point'):
        return self._x == other.x and self._y == other.y

    def __str__(self):
        return f"Point({self._x}, {self._y})"

    __repr__ = __str__

    @property
    def X(self):
        return Point(self._x, 0)

    @property
    def Y(self):
        return Point(0, self._y)

    @property
    def tuple(self):
        return self._x, self._y

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value

    def rotate_around(self, pivot: Point, angle: float):
        theta = math.radians(angle)

        x_new = pivot.x + (self._x - pivot.x) * math.cos(theta) - (self._y - pivot.y) * math.sin(theta)
        y_new = pivot.y + (self._x - pivot.x) * math.sin(theta) + (self._y - pivot.y) * math.cos(theta)
        return x_new, y_new

    def distance(self, other: Point):
        return math.sqrt((self._x - other.x) ** 2 + (self._y - other.y) ** 2)

    def int(self):
        return PointInt(self)


class PointInt(Point):
    def __init__(self, x, y=None):
        if isinstance(x, Point):
            y = x.y
            x = x.x
        super().__init__(int(x), int(y))

    def __str__(self):
        return f"PointInt({self._x}, {self._y})"

    @property
    def x(self):
        return int(self._x)

    @property
    def y(self):
        return int(self._y)