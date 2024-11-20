from .point import Point


class Rect:
    def __init__(self, x, y, width, height):
        self._x = x
        self._y = y
        self._width = width
        self._height = height

    @property
    def top(self):
        return self._y

    @property
    def bottom(self):
        return self._y + self._height

    @property
    def left(self):
        return self._x

    @property
    def right(self):
        return self._x + self._width

    @property
    def top_left(self):
        return Point(self._x, self._y)

    @property
    def top_right(self):
        return Point(self._x + self._width, self._y)

    @property
    def bottom_left(self):
        return Point(self._x, self._y + self._height)

    @property
    def bottom_right(self):
        return Point(self._x + self._width, self._y + self._height)

    def intersected(self, other: 'Rect'):
        """
        Проверяет, пересекаются ли два прямоугольника.

        Аргументы:
        other -- другой прямоугольник

        Возвращает:
        True, если прямоугольники пересекаются, иначе False
        """
        return not (self.right < other.left or self.left > other.right or
                    self.bottom < other.top or self.top > other.bottom)

    def contains(self, point: Point|list|tuple):
        """
        Проверяет, содержит ли прямоугольник указанную точку.

        Аргументы:
        point -- точка для проверки

        Возвращает:
        True, если прямоугольник содержит точку, иначе False
        """
        if isinstance(point, (list, tuple)):
            assert len(point) == 2, 'Point must be a list or tuple of length 2'
            point = Point(*point)
        return (self.left <= point.x <= self.right and
                self.top <= point.y <= self.bottom)

    def map_point_to(self, point: Point, other_rect: 'Rect'):
        """
        Мапит координаты точки в своих локальных координатах в локальные координаты другого прямоугольника.

        Аргументы:
        point -- точка для маппинга
        other_rect -- другой прямоугольник

        Возвращает:
        Точку с координатами в локальных координатах другого прямоугольника
        """
        local_x = point.x - self.left
        local_y = point.y - self.top
        mapped_x = other_rect.left + local_x
        mapped_y = other_rect.top + local_y
        return Point(mapped_x, mapped_y)

    def corners(self, as_tuple=True):
        values = self.top_right.tuple, self.bottom_left.tuple
        if as_tuple:
            return tuple(x.tuple for x in values)
        return values

    def point(self, as_tuple=True):
        values = self.top_left, self.top_right, self.bottom_right, self.bottom_left
        if as_tuple:
            return tuple(x.tuple for x in values)
        return values

    def line(self, as_tuple=True):
        values = self.top_left, self.top_right, self.bottom_right, self.bottom_left, self.top_left
        if as_tuple:
            return tuple(x.tuple for x in values)
        return values

    def adjusted(self, left, top, right, bottom):
        return Rect(
            self._x + left,
            self._y + top,
            self._width - left - right,
            self._height - top - bottom
        )


    def __str__(self):
        return f"Rect({self._x}, {self._y}, {self._width}, {self._height})"

    __repr__ = __str__