from __future__ import absolute_import

from itertools import chain

from .base_shape import BaseShape, EmptyShape
from frame_stamp.utils.exceptions import PresetError
from frame_stamp.utils import cached_result, geometry_tools

import logging

from ..utils.geometry_tools import rect_in_canvas
from ..utils.rect import Rect

logger = logging.getLogger(__name__)


class TileShape(BaseShape):
    shape_name = 'tile'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._shapes = self._init_shapes(**kwargs)

    @property
    def rotate(self):
        """Tile rotation not supported. use grid_rotate"""
        return 0

    @property
    @cached_result
    def grid_rotate(self):
        return self._eval_parameter('grid_rotate', default=0)

    @property
    @cached_result
    def vertical_spacing(self):
        return self._eval_parameter('vertical_spacing', default=None) or self._eval_parameter('v_spacing', default=None)

    @property
    @cached_result
    def horizontal_spacing(self):
        return self._eval_parameter('horizontal_spacing', default=None) or self._eval_parameter('h_spacing', default=None)

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
    def max_rows(self):
        return self._eval_parameter('max_rows', default=None)

    @property
    @cached_result
    def max_columns(self):
        return self._eval_parameter('max_columns', default=None)

    @property
    @cached_result
    def random_order(self):
        return self._eval_parameter('random_order', default=False)

    @property
    @cached_result
    def random_seed(self):
        return self._eval_parameter('random_seed', default=0)

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

    def render(self, size, **kwargs):
        shapes = self.iter_shapes()
        spacing = list(self.spacing)
        if self.horizontal_spacing is not None:
            spacing[0] = self.horizontal_spacing
        if self.vertical_spacing is not None:
            spacing[1] = self.vertical_spacing
        coords = self.generate_coords(self.parent.size, [self.tile_width, self.tile_height],
                                      rotate=-self.grid_rotate, pivot=self.pivot, spacing=spacing,
                                      rows_offset=self.row_offset, columns_offset=self.column_offset,
                                      max_rows=self.max_rows, max_columns=self.max_columns
                                      )

        canvas_width, canvas_height = size
        index = 0
        for i, tile in enumerate(coords):
            rot_pivot = (tile[0]+(self.tile_width/2), tile[1] + (self.tile_height/2))
            parent = EmptyShape({'x': tile[0], 'y': tile[1],
                                 'rotate': self.grid_rotate,
                                 'rotation_pivot': rot_pivot,
                                 "pivot": self.pivot,
                                 "w": self.tile_width, "h": self.tile_height},
                                self.context)

            sh: BaseShape = next(shapes)
            sh.clear_cache()
            sh.set_parent(parent)
            sh.update_local_context(tile_index=index, global_index=i)

            rotated_rect_points = list(sh.raw_rect.rotate(-sh.global_rotate, rot_pivot))
            is_visible = rect_in_canvas(rotated_rect_points, canvas_width, canvas_height)

            if is_visible:
                yield from sh.render(size)
                index += 1

    def __render(self, size, **kwargs):
        shapes = self.iter_shapes()
        spacing = list(self.spacing)
        if self.horizontal_spacing is not None:
            spacing[0] = self.horizontal_spacing
        if self.vertical_spacing is not None:
            spacing[1] = self.vertical_spacing
        coords = self.generate_coords(self.parent.size, [self.tile_width, self.tile_height],
                                      rotate=self.grid_rotate, pivot=self.pivot, spacing=spacing,
                                      rows_offset=self.row_offset, columns_offset=self.column_offset,
                                      max_rows=self.max_rows, max_columns=self.max_columns
                                      )
        main_rect = (
            (0, 0),
            (size[0] - 1, 0),
            (size[0] - 1, size[1] - 1),
            (0, size[1] - 1))

        dump_data = {'points':coords, 'rect': main_rect, 'bounds': []}

        drawing = skipped = 0
        if self.random_order:
            import random
            random.seed(self.random_seed + len(coords))
            random.shuffle(coords)
        index = 0
        for i, tile in enumerate(coords):
            parent = EmptyShape({'x': tile[0], 'y': tile[1],
                                 'rotate': -self.grid_rotate,
                                 'rotation_pivot': tile,
                                 "pivot": self.pivot,
                                 "w": self.tile_width, "h": self.tile_height},
                                 self.context)

            sh: BaseShape = next(shapes)
            sh.clear_cache()
            sh.set_parent(parent)
            sh.update_local_context(tile_index=index, global_index=i)
            bound: Rect = tuple(sh.rotated_rect)
            if i == 231:
                print(bound)
            dump_data['bounds'].append(bound)
            if geometry_tools.rectangles_intersect(bound, main_rect):
                yield from sh.render(size)
                drawing += 1
                index += 1
            else:
                if i == 231:
                    print('SKIP', i, index, bound, main_rect, sh.rotate)
                skipped += 1
        logging.debug(f'Drawing: {drawing}, skipped: {skipped}')
        import json
        with open('coords.json', 'w') as f:
            json.dump(dump_data, f, indent=2)

    def generate_coords(self, rect_size, tile_size,
                        rotate=0, pivot=None,
                        spacing=None,
                        rows_offset=0, columns_offset=0,
                        max_rows=None, max_columns=None):

        if spacing is None:
            spacing = [0.0, 0.0]
        if tile_size[0] == 0 or tile_size[1] == 0:
            raise ValueError("Tile size or tile scale cannot be zero.")

        max_w = max(rect_size)
        max_w_x = max_w - (max_w % tile_size[0])
        max_w_y = max_w - (max_w % tile_size[1])

        if pivot is None:
            pivot = [0, 0]
        start_point = [
            (pivot[0] % max_w_x) - 2 * max_w_x,
            (pivot[1] % max_w_y) - 2 * max_w_y
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
            rows = []
            while x < end_point[0]:
                column_offset = columns_offset if column_count % 2 == 1 else 0
                rows.append((x + row_offset, y + column_offset))
                x += tile_size[0] + spacing[0]
                column_count += 1
            coordinates.append(rows)
            y += tile_size[1] + spacing[1]
            row_count += 1
            column_count = 0
        coords = geometry_tools.remove_excess_elements(coordinates, max_rows, max_columns, pivot)
        sorted_coords = tuple(chain(*sorted([sorted(row) for row in coords], key=lambda row: row[0])))
        rotated_coord = [geometry_tools.rotate_point(coord, rotate, pivot) for coord in sorted_coords]
        return rotated_coord


