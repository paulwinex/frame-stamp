from .base_shape import BaseShape
from PIL import ImageDraw, Image
from frame_stamp.utils import cached_result, geometry_math


class RectShape2(BaseShape):
    """
    Прямоугольник

    Allowed parameters:
        border_width    : толщина обводки
        border_color    : цвет обводки
    """
    shape_name = 'rect2'

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

    ############
    # def max_distance_from_center(self):
    #     return (self.width ** 2 + self.height ** 2) ** 0.5 / 2

    # def rotate_point_around_point(self, point, center, angle):
    #     """
    #     Рассчитывает вектор смещения точки после поворота вокруг другой точки на заданный угол.
    #
    #     Аргументы:
    #     point -- кортеж с координатами точки, которую нужно повернуть (x, y)
    #     center -- кортеж с координатами центра поворота (cx, cy)
    #     angle -- угол поворота в градусах
    #
    #     Возвращает:
    #     Кортеж с вектором смещения (dx, dy)
    #     """
    #     import math
    #
    #     theta = math.radians(angle)
    #     x, y = point
    #     cx, cy = center
    #     x_new = cx + (x - cx) * math.cos(theta) - (y - cy) * math.sin(theta)
    #     y_new = cy + (x - cx) * math.sin(theta) + (y - cy) * math.cos(theta)
    #     return x_new, y_new
    #     # return x_new - x, y_new - y

    def render(self, size, **kwargs):
        if not self.is_enabled():
            return self._get_canvas(size)
        # compute current shape canvas size including rotation
        max_size = int(self.max_distance_from_center() * 2.2)
        render_size = (int(max_size), int(max_size))
        # create shape canvas
        overlay = self._get_canvas(render_size)
        img = ImageDraw.Draw(overlay)
        # render shape to center
        center = max_size / 2
        render_x = center - (self.width / 2)
        render_y = center - (self.height / 2)
        img.rectangle(
            ((render_x, render_y), (render_x + self.width, render_y + self.height)),
            self.color)
        # rotate
        if self.rotate:
            # rotate around center
            overlay = overlay.rotate(self.rotate, expand=False, center=(center, center), resample=Image.BICUBIC)
        # compute coords for pasting
        paste_x = self.x-render_x
        paste_y = self.y-render_y
        # compute transformation offset for rotated shape
        if self.rotate:
            pivot_x, pivot_y = self.rotate_pivot
            pivot_x += self.x
            pivot_y += self.y
            rotated_x, rotated_y = geometry_math.rotate_point_around_point(
                self.center,
                (pivot_x, pivot_y),
                -self.rotate)
            # move rotated shape
            paste_x += (rotated_x- self.center_x)
            paste_y += (rotated_y- self.center_y)
        # paste to main canvas
        main_canvas = self._get_canvas(size)
        main_canvas.paste(overlay, (int(paste_x), int(paste_y)))

        if self._debug:
            main_canvas = self._render_debug(main_canvas, size)
        return main_canvas



    def __render(self, size, **kwargs):
        if not self.is_enabled():
            return self._get_canvas(size)
        # compute current shape canvas size including rotation
        max_size = int(self.max_distance_from_center() * 2.2)
        render_size = (int(max_size), int(max_size))
        # print(f'{self.width=}   {self.height=}')
        # print(f'{max_size=} ({self.max_distance_from_center()})')
        # create shape canvas
        overlay = self._get_canvas(render_size)
        img = ImageDraw.Draw(overlay)
        # render shape to center
        center = max_size / 2
        render_x = center - (self.width / 2)
        render_y = center - (self.height / 2)
        # print(f'{render_x=}x{render_y=}')
        img.rectangle(
            ((render_x, render_y), (render_x + self.width, render_y + self.height)),
            self.color)
        # rotate
        print(f'{self.rotate_pivot=}')
        if self.rotate and self._eval_parameter('apply_offset', default=True):
            overlay = overlay.rotate(self.rotate, expand=False, center=(center, center), resample=Image.BICUBIC)

        # debug lines
        img = ImageDraw.Draw(overlay)
        img.line([
            (0, 0),
            (max_size-1, 0),
            (max_size-1, max_size-1),
            (0, max_size-1),
            (0, 0)
        ], 'yellow', 1)
        # rotate
        # ...
        # compute offset for pasting
        # move to main canvas

        main_canvas = self._get_canvas(size)
        paste_x = self.x-render_x
        paste_y = self.y-render_y
        print(f'Paste 1: {paste_x=} {paste_y=}')

        if self.rotate and self._eval_parameter('apply_offset', default=True):
            rotated_x, rotated_y = self.rotate_point_around_point(
                (center, center),
                (render_x+self.rotate_pivot[0], render_y+self.rotate_pivot[1]),
                -self.rotate)
            paste_x += (rotated_x-render_x)
            paste_y += (rotated_y-render_y)
            print(f'Paste 2: {paste_x=} {paste_y=}')

        main_canvas.paste(overlay, (int(paste_x), int(paste_y)))
        # rotate around center
        # compute transformations
        # move rotated shape

        # result = self.draw_shape(size, **kwargs)
        # if self._debug:
        #     result = self._render_debug(result, size)
        # result = self._apply_rotate(result)
        return main_canvas



    def draw_shape(self, **kwargs):
        max_size = int(self.max_distance_from_center() * 1.1)
        # size = max((max_size, size[0])), max((max_size, size[1]))
        render_size = (int(max_size), int(max_size))
        center_x = render_size[0] / 2# - (self.width_draw // 2)
        center_y = render_size[1] / 2# - (self.height_draw // 2)
        render_x = center_x - (self.width / 2)
        render_y = center_y - (self.height / 2)
        # draw shape in center
        print(f'{render_size=}')
        print(f'{center_x=}   {center_y=}')
        print(f'{render_x=}   {render_y=}')
        print(f'{self.width_draw=}   {self.height_draw=}')
        # print(f'{self.padding_right=}  {self.padding_left=}  {self.padding_top=}  {self.padding_bottom=}')
        print(f'{self.x_draw=}   {self.y_draw=}')
        print(f'{self.width=}   {self.height=}')
        # print(f'{self.x=}   {self.y=}')
        print(f'{self.x0=}   {self.y0=}')
        print(f'{self.x1=}   {self.y1=}')
        print(f'{self.left=}   {self.top=}')
        print(f'{self.right=}   {self.bottom=}')
        print(f'{self.center_x=}   {self.center_y=}')
        print(f'{self.center=}')
        print(f'{self.rotate=}   {self.rotate_pivot=}')

        overlay = self._get_canvas(render_size)
        img = ImageDraw.Draw(overlay)
        # x = render_size[0]/2 - (self.width_draw//2)
        # y = render_size[1]/2 - (self.height_draw//2)
        print(f'Shape Rect: {render_x} x {render_y} / {render_x+self.width} x {render_y+self.height}')

        img.rectangle(
            # ((x, y), (x+self.width_draw, y+self.height_draw)),
            ((render_x, render_y), (render_x+self.width, render_y+self.height)),
            self.color)
        # border = self.border_width
        # if border:
        #     points = [
        #         (self.left, self.top),
        #         (self.right, self.top),
        #         (self.right, self.bottom),
        #         (self.left, self.bottom),
        #         (self.left, self.top)
        #     ]
        #     img.line(points, self.border_color, self.border_width)
        return overlay



def rotate_point_around_point(point, center, angle):
    """
    Поворачивает точку вокруг другой точки на заданный угол.

    Аргументы:
    point -- кортеж с координатами точки, которую нужно повернуть (x, y)
    center -- кортеж с координатами центра поворота (cx, cy)
    angle -- угол поворота в градусах

    Возвращает:
    Кортеж с новыми координатами точки после поворота (x_new, y_new)
    """
    import math
    # Преобразуем угол в радианы
    theta = math.radians(angle)

    # Распаковываем координаты точки и центра
    x, y = point
    cx, cy = center

    # Вычисляем новые координаты точки после поворота
    x_new = cx + (x - cx) * math.cos(theta) - (y - cy) * math.sin(theta)
    y_new = cy + (x - cx) * math.sin(theta) + (y - cy) * math.cos(theta)

    return (x_new, y_new)
# rotate_point_around_point((100, 100), (100, 100), 45)