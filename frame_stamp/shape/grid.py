from __future__ import absolute_import
from .base_shape import BaseShape, EmptyShape
from frame_stamp.utils.exceptions import PresetError
from frame_stamp.utils import cached_result
from PIL import Image
import cgflogging

logger = cgflogging.getLogger(__name__)


class GridShape(BaseShape):
    """
    Составная фигура в виде Таблицы.

    Allowed parameters:
        rows           : Количество строк
        columns        : Количество колонок
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
        from frame_stamp.shape import get_shape_class
        for i, shape_config in enumerate(shape_list):
            if not shape_config:
                continue
            shape_type = shape_config.get('type')
            if shape_type is None:
                raise PresetError('Shape type not defined in template element: {}'.format(shape_config))
            cells[i]['parent'] = self
            lc = {'index': i, 'row': cells[i]['row'], 'column': cells[i]['column']}
            shape_config['parent'] = EmptyShape(cells[i], self.context, local_context=lc)
            shape_cls = get_shape_class(shape_type)
            shape = shape_cls(shape_config, self.context, local_context=lc, **kwargs)
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
    def rows(self):
        return self._eval_parameter('rows', default='auto')

    @property
    @cached_result
    def max_row_height(self):
        return self._eval_parameter('max_row_height', default=0)

    @property
    @cached_result
    def max_column_width(self):
        return self._eval_parameter('max_column_width', default=0)

    @property
    @cached_result
    def columns(self):
        return self._eval_parameter('columns', default='auto')

    @property
    @cached_result
    def fit_to_content_height(self):
        return bool(self._eval_parameter('fit_to_content_height', default=True))

    def _fix_cell_height(self):
        from collections import defaultdict
        # собираем высоты всех элементов группируя по строкам
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
        # применяем изменения построчно
        for row, data in new_row_data.items():
            for s in self._shapes:
                if s._local_context['row'] == row:
                    s.parent._data['y'] += data['offs']
                    s.parent._data['height'] = s.parent._data['h'] = data['height']
                    s.parent.__cache__.clear()
                    s.__cache__.clear()

    def generate_cells(self, count, cols=None, rows=None):
        # todo: выравнивание неполных строк и колонок
        if not count:
            return
        cells = []
        # рассчитываем количество строк и колонок
        columns = cols or self.columns
        rows = rows or self.rows
        if columns == 'auto' and rows == 'auto':
            columns = rows = count/2
        elif columns == 'auto':
            columns = count//rows or 1
        elif rows == 'auto':
            rows = count//columns or 1
        # общая ширина, занимаемая колонками
        all_h_spacing = self.horizontal_spacing * (columns-1)
        cells_width = self.width - self.padding_left - self.padding_right - all_h_spacing
        one_cell_width = cells_width / columns
        if self.max_column_width:
            one_cell_width = min([one_cell_width, self.max_column_width])
        # общая ширина, занимаемая строками
        all_v_spacing = self.vertical_spacing * (rows-1)
        cells_height = self.height - self.padding_bottom - self.padding_top - all_v_spacing
        one_cell_height = cells_height // rows
        height_limit = self.max_row_height
        if height_limit:
            one_cell_height = min([one_cell_height, height_limit])
        # паддинги
        h_space = self.horizontal_spacing
        v_space = self.vertical_spacing
        h_pad = self.padding_left
        v_pad = self.padding_top
        # рассчитываем ячейки
        for i in range(count):
            col = i % columns
            row = i//columns
            cells.append(dict(
                x=h_pad + ((one_cell_width + h_space) * col),
                y=v_pad + ((one_cell_height+v_space)*row),
                width=one_cell_width,
                height=one_cell_height,
                column=col,
                row=row
            ))
        return cells

    def get_cell_shapes(self):
        return self._shapes

    def draw_shape(self, size, **kwargs):
        canvas = self._get_canvas(size)
        shapes = self.get_cell_shapes()
        if shapes:
            for shape in self.get_cell_shapes():
                # if shape._local_context['row'] == 1:
                #     print(shape._data, shape.y, shape.y_draw)
                overlay = shape.render(size)
                canvas = Image.alpha_composite(canvas, overlay)
        return canvas
