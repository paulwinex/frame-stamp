from __future__ import absolute_import
from .base_shape import BaseShape, EmptyShape
from frame_stamp.utils.exceptions import PresetError
from frame_stamp.utils import cached_result
from PIL import Image, ImageDraw
import logging

from ..utils.point import Point

logger = logging.getLogger(__name__)


class GridShape(BaseShape):
    """
    Combined shape - grid

    Allowed parameters:
        rows           : Row count
        columns        : Columns count
    """
    shape_name = 'grid'

    def __init__(self, *args, **kwargs):
        super(GridShape, self).__init__(*args, **kwargs)
        self._shapes = self._create_shapes_from_data(**kwargs)
        if self.fit_to_content_height:
            self._fix_cell_height()

    def _create_shapes_from_data(self, **kwargs):
        if self.width == 0:
            logger.warning('Grid width is 0')
        if self.height == 0:
            logger.warning('Grid height is 0')
        shapes = []
        shape_list = self._data.get('shapes')
        if not shape_list:
            return []
        cells = self.generate_cells(len(shape_list))
        self.c = cells
        from frame_stamp.shape import get_shape_class
        offs = 0
        for i, shape_config in enumerate(shape_list):
            if not shape_config:
                continue
            shape_type = shape_config.get('type')
            if shape_type is None:
                raise PresetError('Shape type not defined in template element: {}'.format(shape_config))
            cells[i]['parent'] = self
            lc = {'cell_index': i+offs, 'row': cells[i+offs]['row'], 'column': cells[i+offs]['column']}
            shape_config['parent'] = EmptyShape(cells[i+offs], self.context, local_context=lc)
            shape_cls = get_shape_class(shape_type)
            kwargs['local_context'] = lc
            shape = shape_cls(shape_config, self.context, **kwargs)
            if shape.skip:
                offs -= 1
                continue
            shapes.append(shape)
            if shape.id is not None:
                if shape.id in self.scope:
                    raise PresetError('Duplicate shape ID: {}'.format(shape.id))
            self.add_shape(shape)
        return shapes

    @property
    @cached_result
    def vertical_spacing(self):
        return self._eval_parameter('vertical_spacing', default=0)

    @property
    @cached_result
    def horizontal_spacing(self):
        return self._eval_parameter('horizontal_spacing', default=0)

    @property
    @cached_result
    def padding(self):
        param = self._eval_parameter('padding', default=(0, 0, 0, 0))
        if isinstance(param, (int, float)):
            param = (param, param, param, param)
        if not isinstance(param, (list, tuple)):
            raise TypeError('Padding parameter must be list or tuple')
        if len(param) != 4:
            raise ValueError('Padding parameter must be size = 4')
        return tuple(map(int, param))

    @property
    @cached_result
    def padding_top(self):
        return int(self._eval_parameter('padding_top', default=None) or self.padding[0])

    @property
    @cached_result
    def padding_right(self):
        return int(self._eval_parameter('padding_right', default=None) or self.padding[1])

    @property
    @cached_result
    def padding_bottom(self):
        return int(self._eval_parameter('padding_bottom', default=None) or self.padding[2])

    @property
    @cached_result
    def padding_left(self):
        return int(self._eval_parameter('padding_left', default=None) or self.padding[3])

    @property
    @cached_result
    def rows(self):
        return self._eval_parameter('rows', default='auto')

    @property
    @cached_result
    def max_row_height(self):
        return self._eval_parameter('max_row_height', default=0)

    @property
    @cached_result
    def columns(self):
        return self._eval_parameter('columns', default='auto')

    @property
    def rotate(self):
        if super().rotate:
            logger.warning('Grid shape does not support rotation')
        return 0

    @property
    @cached_result
    def columns_width(self):
        val = self._eval_parameter('columns_width', default=self.width, skip_type_convert=True)
        if isinstance(val, dict):
            # here is a tricky way to parse a dictionary
            # - this parameter can only be a dictionary
            # - the key is a number in the form of a string, the column index. you can specify a negative value (index from the end)
            # - the value is any expression but its result must be a number
            return {int(k): int(self._eval_parameter_convert('', v, default=self.width)) for k, v in val.items()}
        return None

    @property
    @cached_result
    def fit_to_content_height(self):
        return bool(self._eval_parameter('fit_to_content_height', default=True))

    def _fix_cell_height(self):
        from collections import defaultdict
        # collect the heights of all elements by grouping them by rows
        heights = defaultdict(list)
        for shape in self._shapes:
            heights[shape._local_context['row']].append(shape.height)
        new_row_data = defaultdict(dict)
        curr_offset = 0
        for row, sizes in heights.items():
            max_shape_height = max(sizes)
            curr_row_height = max([s.parent.height for s in self._shapes if s._local_context['row'] == row])
            new_row_data[row]['offs'] = curr_offset
            if max_shape_height > curr_row_height:
                curr_offset += max_shape_height - curr_row_height
                new_row_data[row]['height'] = max_shape_height
            else:
                new_row_data[row]['height'] = curr_row_height
        # apply changes line by line
        for row, data in new_row_data.items():
            for s in self._shapes:
                if s._local_context['row'] == row:
                    s.parent._data['y'] += data['offs']
                    s.parent._data['height'] = s.parent._data['h'] = data['height']
                    s.parent.__cache__.clear()
                    s.__cache__.clear()

    def _adjust_columns_width(self, columns):
        custom_columns_width = self.columns_width
        if not custom_columns_width:
            return columns
        # total width of columns
        full_columns_width = sum(columns.values())
        # replace negative indices with absolute ones
        _filtered = {}
        for c, val in custom_columns_width.items():
            if c < 0:
                if abs(c) > len(columns):
                    # index too big
                    continue
                _filtered[len(columns) + c] = val
            else:
                if c > len(columns)-1:
                    # index too big
                    continue
                _filtered[c] = val
        custom_columns_width = _filtered
        # column width with unlimited size
        free_size_columns = [x for x in range(len(columns)) if
                             x not in custom_columns_width]  # columns that did not have their size fixed
        if free_size_columns:
            # unlimited columns divide the remaining width equally
            fixed_size = sum(custom_columns_width.values())
            free_size = full_columns_width - fixed_size
            free_columns_width = free_size / len(free_size_columns)
        else:
            free_columns_width = 0
        # update the column width in the list
        for i in range(len(columns)):
            if i in custom_columns_width:
                columns[i] = max([1,custom_columns_width[i]])
            else:
                columns[i] = max([1, free_columns_width])
        return columns

    def generate_cells(self, count, cols=None, rows=None):
        # todo: выравнивание неполных строк и колонок
        if not count:
            return
        cells = []
        # we calculate the number of rows and columns
        columns = cols or self.columns
        rows = rows or self.rows
        if columns == 'auto' and rows == 'auto':
            columns = rows = count/2
        elif columns == 'auto':
            columns = count//rows or 1
        elif rows == 'auto':
            rows = count//columns or 1
        #total width occupied by columns
        all_h_spacing = self.horizontal_spacing * (columns-1)
        cells_width = self.width - self.padding_left - self.padding_right - all_h_spacing
        one_cell_width = cells_width / columns  # the width of one column if all columns are the same
        all_columns_width = {x: one_cell_width for x in range(columns)}
        # calculation of individual width
        all_columns_width = self._adjust_columns_width(all_columns_width)
        # recalculation of X coordinates
        all_columns_x = {}
        curr = 0
        for col, w in all_columns_width.items():
            # here each column starts after the previous one. Indents will be added later
            all_columns_x[col] = curr
            curr += w

        # total height occupied by lines
        all_v_spacing = self.vertical_spacing * (rows-1)
        cells_height = self.height - self.padding_bottom - self.padding_top - all_v_spacing
        one_cell_height = cells_height // rows
        height_limit = self.max_row_height
        if height_limit:
            one_cell_height = min([one_cell_height, height_limit])
        # paddings
        h_space = self.horizontal_spacing
        v_space = self.vertical_spacing
        h_pad = self.padding_left
        v_pad = self.padding_top
        # calculate cells
        for i in range(count):
            col = i % columns
            row = i//columns
            col_width = all_columns_width[col]  # current column width
            col_x = all_columns_x[col]          # X coordinate
            cells.append(dict(
                x=h_pad + col_x + (h_space*col),
                y=v_pad + ((one_cell_height+v_space)*row),
                width=col_width,
                height=one_cell_height,
                column=col,
                row=row
            ))
        return cells

    def get_cell_shapes(self):
        return self._shapes

    @property
    @cached_result
    def border(self):
        value = self._eval_parameter('border', default=None)
        if value is None:
            return {}
        assert isinstance(value, dict), 'Border value must be a dict'
        value.setdefault('enabled', True)
        value.setdefault('width', 1)
        value.setdefault('color', 'black')
        if isinstance(value['color'], list):
            value['color'] = tuple(value['color'])
        return value

    @property
    @cached_result
    def border_width(self):
        return self._eval_parameter('border_width', default=0)

    @property
    @cached_result
    def border_color(self):
        return self._eval_parameter('border_color', default='black')

    def render(self, size, **kwargs):
        from frame_stamp.utils.rect import Rect

        shapes = self.get_cell_shapes()
        if shapes and self.is_enabled():
            for shape in shapes:
                yield from shape.render(size, **kwargs)
        if self.border.get('enabled') and self.is_enabled():
            offset_top = self.border.get('offset_top', self.border.get('offset', 0))
            offset_bottom = self.border.get('offset_bottom', self.border.get('offset', 0))
            offset_left = self.border.get('offset_left', self.border.get('offset', 0))
            offset_right = self.border.get('offset_right', self.border.get('offset', 0))
            max_offset = max((abs(offset_top), abs(offset_bottom), abs(offset_left), abs(offset_right)))+(self.border['width']*2)
            for i, shape in enumerate(shapes):
                border_rect = Rect(max_offset, max_offset,
                                   shape.parent.width, shape.parent.height)
                canvas = self._get_canvas((border_rect.width + (max_offset*2), border_rect.height + (max_offset*2)))
                border_rect = border_rect.adjusted(offset_left, offset_top, offset_right, offset_bottom)
                drw = ImageDraw.Draw(canvas)
                drw.line(border_rect.line(), fill=self.border['color'], width=self.border['width'])
                offset_pt = Point(max_offset, max_offset)
                yield canvas, shape.parent.pos - offset_pt
