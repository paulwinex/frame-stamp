from __future__ import absolute_import

import math
from itertools import cycle
from .base_shape import BaseShape, EmptyShape
from frame_stamp.utils.exceptions import PresetError
from frame_stamp.utils import cached_result, rotate_point
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class TileShape(BaseShape):
    shape_name = 'tile'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._shapes = self._init_shapes(**kwargs)
        # self._shape_rotate = super().rotate

    @property
    def rotate(self):
        return 0

    @property
    @cached_result
    def grid_rotate(self):
        return self._eval_parameter('grid_rotate', default=0)


    @property
    @cached_result
    def vertical_spacing(self):
        return self._eval_parameter('vertical_spacing', default=0)

    @property
    @cached_result
    def pivot(self):
        return self._eval_parameter('pivot', default=(0,0))

    @property
    @cached_result
    def spacing(self):
        return self._eval_parameter('spacing', default=(0,0))

    @property
    @cached_result
    def horizontal_spacing(self):
        return self._eval_parameter('horizontal_spacing', default=0)


    @property
    @cached_result
    def tile_width(self):
        return self._eval_parameter('tile_width', default=100)

    @property
    @cached_result
    def tile_height(self):
        return self._eval_parameter('tile_height', default=100)

    @property
    @cached_result
    def row_offset(self):
        return self._eval_parameter('row_offset', default=0)

    @property
    @cached_result
    def column_offset(self):
        return self._eval_parameter('column_offset', default=0)

    @property
    @cached_result
    def tile_count_limit(self):
        return self._eval_parameter('tile_count_limit', default=1000)

    @property
    @cached_result
    def limit_count_from_center(self):
        return self._eval_parameter('limit_count_from_center', default=False)

    def ___init_shapes(self, **kwargs):
        from frame_stamp.shape import get_shape_class

        shape_list = self._data.get('shapes')
        if not shape_list:
            return []
        # coords = self.generate_coords(shape_list, self.source_image.size)

        coords = self.generate_coords(self.source_image.size,[self.tile_width, self.tile_height],
                                      rotate=self.grid_rotate, pivot_offset=self.pivot, spacing=self.spacing,
                                      tile_count_limit=self.tile_count_limit,
                                      rows_offset=self.row_offset,
                                      columns_offset=self.column_offset,
                                      limit_count_from_center=self.limit_count_from_center,
                                      )
        shapes = []
        shape_generator = cycle(shape_list)
        for i, tile in enumerate(coords):
            shape_config = next(shape_generator)
            # print('Shape:', shape_config)
            if not shape_config:
                continue
            shape_type = shape_config.get('type')
            if shape_type is None:
                raise PresetError('Shape type not defined in template element: {}'.format(shape_config))
            # parent_shape_config = {**shape_config, **tile}
            # print(parent_shape_config)
            tile_parameters = {'x': tile[0], 'y': tile[1]}#, 'rotate': self.rotate}
            # parent = EmptyShape(tile, self.context)#, local_context=tile)
            # shape_config['parent'] = parent
            shape_cls = get_shape_class(shape_type)
            shape: BaseShape = shape_cls({**shape_config, **tile_parameters}, self.context, **kwargs)
            # w, h = shape.width, shape.height
            # x = x + w + self.horizontal_spacing
            # y = y + h
            # local_context = {}
            # shape_generator.send()
            # shape_config['parent'] = EmptyShape(cells[i], self.context, local_context=lc)
            # kwargs['local_context'] = local_context

            shapes.append(shape)
            if shape.id is not None:
                if shape.id in self.scope:
                    raise PresetError('Duplicate shape ID: {}'.format(shape.id))
            self.add_shape(shape)
        return shapes

    def ___iter_shape_configs(self):
        from itertools import repeat
        shape_list = self._data.get('shapes')
        if not shape_list:
            raise StopIteration
        return repeat(shape_list)


    # def rotate_point(self, point, pivot, angle):
    #     """Rotate a point around another point by a given angle in degrees."""
    #     print('A', angle)
    #     radians = math.radians(angle)
    #     translated_x = point[0] - pivot[0]
    #     translated_y = point[1] - pivot[1]
    #
    #     x_rotated = (translated_x * math.cos(radians) - translated_y * math.sin(radians)) + pivot[0]
    #     y_rotated = (translated_x * math.sin(radians) + translated_y * math.cos(radians)) + pivot[1]
    #
    #     return (x_rotated, y_rotated)

    def intersects(self, rect1, rect2):
        """Check if two rectangles intersect."""
        return not (rect1[0] > rect2[2] or  # rect1 is to the right of rect2
                    rect1[2] < rect2[0] or  # rect1 is to the left of rect2
                    rect1[1] > rect2[3] or  # rect1 is below rect2
                    rect1[3] < rect2[1])  # rect1 is above rect2

    def generate_coords(self, rect_size, tile_size, rotate=0, pivot_offset=None, spacing=None,
                        tile_count_limit=None, rows_offset=0, columns_offset=0, limit_count_from_center=False):

        if spacing is None:
            spacing = [0.0, 0.0]
        if tile_size[0] == 0 or tile_size[1] == 0:
            raise ValueError("Tile size or tile scale cannot be zero.")

        max_w = max(rect_size)
        max_w_x = max_w - (max_w % tile_size[0])
        max_w_y = max_w - (max_w % tile_size[1])

        if pivot_offset is None:
            pivot_offset = [0, 0]

        start_point = [
            (pivot_offset[0] % max_w_x) - 2 * max_w_x,
            (pivot_offset[1] % max_w_y) - 2 * max_w_y
        ]

        end_point = [
            start_point[0] + 4 * max_w_x,
            start_point[1] + 4 * max_w_y
        ]

        coordinates = []

        row_count = 0
        column_count = 0

        y = start_point[1]
        while y < end_point[1]:
            row_offset = rows_offset if row_count % 2 == 1 else 0
            x = start_point[0]
            while x < end_point[0]:
                column_offset = columns_offset if column_count % 2 == 1 else 0
                coordinates.append((x + row_offset, y + column_offset))
                x += tile_size[0] + spacing[0]
                column_count += 1
            y += tile_size[1] + spacing[1]
            row_count += 1
            column_count = 0

        if tile_count_limit is not None and limit_count_from_center:
            coordinates.sort(key=lambda c: math.hypot(c[0] - pivot_offset[0], c[1] - pivot_offset[1]))
            coordinates = coordinates[:tile_count_limit]

        final_coordinates = []

        for coord in coordinates:
            rotated_coord = rotate_point(coord, rotate, pivot_offset)

            tile_rect = (
                rotated_coord[0] - tile_size[0] / 2,
                rotated_coord[1] - tile_size[1] / 2,
                rotated_coord[0] + tile_size[0] / 2,
                rotated_coord[1] + tile_size[1] / 2
            )

            main_rect_with_buffer = (
                0 - tile_size[0],
                0 - tile_size[1],
                rect_size[0] + tile_size[0],
                rect_size[1] + tile_size[1]
            )

            if self.intersects(tile_rect, main_rect_with_buffer):
                final_coordinates.append(rotated_coord)
        if tile_count_limit is not None and not limit_count_from_center:
            final_coordinates = final_coordinates[:tile_count_limit]

        return final_coordinates


    # def _create_positions_grid(self, shape_list, canvas_size, **kwargs):
    #     """
    #     [
    #         {shape_config, index, row, col}
    #     ]
    #
    #     :param shape_list:
    #     :param canvas_size:
    #     :param kwargs:
    #     :return:
    #     """
    #     from frame_stamp.shape import get_shape_class
    #
    #     tile_overlap = 1
    #     center_x, center_y = self.x % canvas_size[0], self.y % canvas_size[1]
    #     print(f"{center_x=}, {center_y=}")
    #     shapes = []
    #     for shape_config in shape_list:
    #         if not shape_config:
    #             raise ValueError('Shape cannot be empty')
    #         shape_type = shape_config.get('type')
    #         shape_cls = get_shape_class(shape_type)
    #         shape: BaseShape = shape_cls(shape_config, self.context, **kwargs)
    #         shapes.append(shape)
    #     # create
    #     cell_width = max([sh.width for sh in shapes])
    #     print(f"{cell_width=}")
    #     cell_height = max([sh.height for sh in shapes])
    #     print(f"{cell_height=}")
    #     max_shape_dim = max([cell_height, cell_width])
    #     print(f"{max_shape_dim=}")
    #     # max_canvas_dim = max(canvas_size)
    #     # print(f"{max_canvas_dim=}")
    #     max_x_value = canvas_size[0] + (max_shape_dim*tile_overlap)
    #     min_x_value = -(max_shape_dim*tile_overlap)
    #     max_y_value = canvas_size[1] + (max_shape_dim*tile_overlap)
    #     min_y_value = -(max_shape_dim*tile_overlap)
    #     # print(f"{max_coord_value=}")
    #     offset_x = cell_width+self.horizontal_spacing
    #     print(f"{offset_x=}")
    #     offset_y = cell_height+self.vertical_spacing
    #     print(f"{offset_y=}")
    #     # start_x = center_x - (offset_x * (canvas_size[0]//offset_x))
    #     start_x = 0 - (center_x % cell_width) - offset_x
    #     print(f"{start_x=}")
    #     # start_y = center_y - (offset_y * (max_coord_value//(offset_y)))
    #     start_y = 0 - (center_y % cell_height) - offset_y
    #     print(f"{start_y=}")
    #     max_rows = self.max_rows or canvas_size[0]//offset_x
    #     print(f"{max_rows=}")
    #     max_columns = self.max_columns or canvas_size[1]//offset_y
    #     print(f"{max_columns=}")
    #
    #     x, y = start_x, start_y
    #     index = 0
    #     col = 0
    #     row = 0
    #     tiles = []
    #     rot = self._eval_parameter('rotate', default=0)
    #     rot_pivot = (center_x, center_y)
    #     while index < self.tile_count_limit:
    #         index += 1
    #         if rot:
    #             _x, _y = rotate_point((x, y), rot, origin=rot_pivot)
    #             print('COORDS', _x, _y)
    #         else:
    #             _x, _y = x, y
    #         if not any([_x > max_x_value,
    #                     _x < min_x_value,
    #                     _y > max_y_value,
    #                     _y < min_y_value]):
    #             tiles.append(dict(
    #                 x=_x,
    #                 y=_y,
    #                 rotate=rot,
    #                 # rotate_pivot=rot_pivot,
    #                 column=col,
    #                 row=row,
    #                 index=index,
    #                 width=cell_width,
    #                 height=cell_height
    #             ))
    #         x += offset_x
    #         col += 1
    #         if x > max_x_value or col+1 > max_columns:
    #             col = 0
    #             row += 1
    #             x = start_x
    #             y += offset_y
    #         if y > max_y_value or row > max_rows:
    #             break
    #     return tiles

    def get_shapes(self):
        return self._shapes

    def _draw_shape(self, size, **kwargs):
        canvas = self._get_canvas(size)
        shapes = self.get_shapes()
        if shapes:
            for shape in shapes:
                # if shape._local_context['row'] == 1:
                #     print(shape._data, shape.y, shape.y_draw)
                overlay = shape.render(size)
                canvas = Image.alpha_composite(canvas, overlay)
        return canvas

    def _init_shapes(self, **kwargs):
        from frame_stamp.shape import get_shape_class

        shapes = []
        shape_list = self._data.get('shapes')
        for shape_config in shape_list:
            shape_type = shape_config.get('type')
            if shape_type is None:
                raise PresetError('Shape type not defined in template element: {}'.format(shape_config))
            shape_cls = get_shape_class(shape_type)
            shape: BaseShape = shape_cls(shape_config, self.context, **kwargs)
            if shape.id:
                raise PresetError('Shape ID for tiled element is not allowed: {}'.format(shape.id))
            shapes.append(shape)
        return shapes

    def iter_shapes(self):
        from itertools import cycle

        if not self._shapes:
            raise StopIteration
        return cycle(self._shapes)


    def draw_shape(self, size, **kwargs):
        canvas: Image.Image = self._get_canvas(size)
        shapes = self.iter_shapes()
        coords = self.generate_coords(self.source_image.size, [self.tile_width, self.tile_height],
                                      rotate=self.grid_rotate, pivot_offset=self.pivot, spacing=self.spacing,
                                      tile_count_limit=self.tile_count_limit,
                                      rows_offset=self.row_offset,
                                      columns_offset=self.column_offset,
                                      limit_count_from_center=self.limit_count_from_center,
                                      )
        for i, tile in enumerate(coords):
            parent = EmptyShape({'x': tile[0], 'y': tile[1], 'rotate': -self.grid_rotate, "w": self.tile_width, "h": self.tile_height}, self.context)
            sh: BaseShape = next(shapes)
            sh.clear_cache()
            sh.set_parent(parent)
            overlay = sh.render(size)
            canvas = Image.alpha_composite(canvas, overlay)
        return canvas