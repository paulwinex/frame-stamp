from __future__ import absolute_import

import math
from email.policy import default
from itertools import chain
from os import PRIO_PGRP

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

    def _render_debug(self, default_render, size):
        from PIL import ImageDraw

        img = super()._render_debug(default_render, size)
        draw = ImageDraw.Draw(img)
        draw.circle(self.pivot, self.point/2,'red')
        return img

    @property
    def rotate(self):
        """Tile rotation not supported. use grid_rotate"""
        return 0

    @property
    @cached_result
    def grid_rotate(self):
        return self._eval_parameter('grid_rotate', default=3)

    @property
    @cached_result
    def vertical_spacing(self):
        return self._eval_parameter('vertical_spacing', default=None)

    @property
    @cached_result
    def horizontal_spacing(self):
        return self._eval_parameter('horizontal_spacing', default=None)

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


    def draw_shape(self, size, **kwargs):
        canvas: Image.Image = self._get_canvas(size)
        shapes = self.iter_shapes()
        spacing = self.spacing
        if self.horizontal_spacing is not None:
            spacing[0] = self.horizontal_spacing
        if self.vertical_spacing is not None:
            spacing[1] = self.vertical_spacing
        coords = self.generate_coords(self.source_image.size, [self.tile_width, self.tile_height],
                                      rotate=self.grid_rotate, pivot=self.pivot, spacing=self.spacing,
                                      rows_offset=self.row_offset,
                                      columns_offset=self.column_offset,
                                      max_rows=self.max_rows, max_columns=self.max_columns
                                      )
        main_rect = (0, 0, size[0], size[1])
        drawing = skipped = 0
        if self.random_order:
            import random
            random.seed(self.random_seed + len(coords))
            random.shuffle(coords)
        index = 0
        for i, tile in enumerate(coords):
            parent = EmptyShape({'x': tile[0], 'y': tile[1],
                                 'rotate': -self.grid_rotate,
                                 'rotate_pivot': tile,
                                 "pivot": self.pivot,
                                 "w": self.tile_width, "h": self.tile_height},
                                self.context)

            sh: BaseShape = next(shapes)
            sh.clear_cache()
            sh.set_parent(parent)
            sh.update_local_context(tile_index=index)
            bound = [sh.x0, sh.y0, sh.x1, sh.y1]
            if self.check_intersection(bound, main_rect):
                overlay = sh.render(size)
                canvas = Image.alpha_composite(canvas, overlay)
                drawing += 1
                index += 1
            else:
                skipped += 1
        logging.debug(f'Drawing: {drawing}, skipped: {skipped}')
        return canvas

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

        coords = self.remove_excess_elements(coordinates, max_rows, max_columns, pivot)
        sorted_coords = tuple(chain(*sorted([sorted(row) for row in coords], key=lambda row: row[0])))
        rotated_coord = [rotate_point(coord, rotate, pivot) for coord in sorted_coords]
        return rotated_coord

    def get_rectangle_points(self, rect, angle=0):
        """Returns the coordinates of the corners of a rectangle, taking into account rotation."""
        x0, y0, x1, y1 = rect
        center_x = (x0 + x1) / 2
        center_y = (y0 + y1) / 2
        points = [
            (x0, y0),
            (x1, y0),
            (x1, y1),
            (x0, y1)
        ]
        if angle != 0:
            points = [rotate_point(point, angle, (center_x, center_y)) for point in points]
        return points

    def separating_axis_theorem(self, rect1, rect2):
        """Tests the intersection of two convex polygons using the separating axis theorem."""
        def get_normals(points):
            """Returns the normals to the sides of a polygon."""
            normal_list = []
            for i in range(len(points)):
                p1 = points[i]
                p2 = points[(i + 1) % len(points)]
                edge = (p2[0] - p1[0], p2[1] - p1[1])
                normal = (-edge[1], edge[0])
                normal_list.append(normal)
            return normal_list

        def project(points, axis):
            """Projects points onto an axis and returns the minimum and maximum values of the projection."""
            min_proj = max_proj = None
            for point in points:
                proj = point[0] * axis[0] + point[1] * axis[1]
                if min_proj is None or proj < min_proj:
                    min_proj = proj
                if max_proj is None or proj > max_proj:
                    max_proj = proj
            return min_proj, max_proj

        points1 = self.get_rectangle_points(rect1)
        points2 = self.get_rectangle_points(rect2)

        for points in [points1, points2]:
            normals = get_normals(points)
            for normal in normals:
                min1, max1 = project(points1, normal)
                min2, max2 = project(points2, normal)
                if max1 < min2 or max2 < min1:
                    return False
        return True

    def check_intersection(self, rect1, rect2, angle1=0, angle2=0):
        """Checks the intersection of two rectangles, taking into account rotation."""
        if angle1 != 0 or angle2 != 0:
            points1 = self.get_rectangle_points(rect1, angle1)
            points2 = self.get_rectangle_points(rect2, angle2)
            return self.separating_axis_theorem(points1, points2)
        else:
            x0_1, y0_1, x1_1, y1_1 = rect1
            x0_2, y0_2, x1_2, y1_2 = rect2
            return not (x1_1 < x0_2 or x1_2 < x0_1 or y1_1 < y0_2 or y1_2 < y0_1)

    def distance(self, point1, point2):
        """Calculates the Euclidean distance between two points."""
        return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

    def get_row_distances(self, matrix, deleting_pivot):
        """Returns a list of distances from each row to the deleting pivot point."""
        row_distances = []
        for row in matrix:
            row_center = [sum(col[0] for col in row) / len(row), sum(col[1] for col in row) / len(row)]
            row_distances.append(self.distance(row_center, deleting_pivot))
        return row_distances

    def get_column_distances(self, matrix, deleting_pivot):
        """Returns a list of distances from each column to the deleting_pivot point."""
        column_distances = []
        for col_idx in range(len(matrix[0])):
            col_center = [sum(row[col_idx][0] for row in matrix) / len(matrix), sum(row[col_idx][1] for row in matrix) / len(matrix)]
            column_distances.append(self.distance(col_center, deleting_pivot))
        return column_distances

    def remove_excess_elements(self, matrix, max_rows, max_columns, deleting_pivot):
        """Removes extra rows and columns from the matrix."""
        if max_rows == 0 or max_columns == 0:
            return []

        row_distances = self.get_row_distances(matrix, deleting_pivot)
        column_distances = self.get_column_distances(matrix, deleting_pivot)

        # Sort row and column indices by distance
        sorted_row_indices = sorted(range(len(row_distances)), key=lambda i: row_distances[i])
        sorted_column_indices = sorted(range(len(column_distances)), key=lambda i: column_distances[i])

        # We leave only max_rows and max_columns
        selected_row_indices = sorted_row_indices[:max_rows] if max_rows is not None else sorted_row_indices
        selected_column_indices = sorted_column_indices[:max_columns] if max_columns is not None else sorted_column_indices

        # Create a new matrix with the selected rows and columns
        new_matrix = []
        for row_idx in selected_row_indices:
            new_row = [matrix[row_idx][col_idx] for col_idx in selected_column_indices]
            new_matrix.append(new_row)

        return new_matrix

