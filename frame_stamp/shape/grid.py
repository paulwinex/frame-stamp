from __future__ import absolute_import
from .base_shape import BaseShape, EmptyShape
from frame_stamp.utils.exceptions import PresetError
from frame_stamp.utils import cached_result
from PIL import Image
import logging

logger = logging.getLogger(__name__)


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
        # if self.columns_width:
        #     self._adjust_columns_width()

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
            lc = {'index': i+offs, 'row': cells[i+offs]['row'], 'column': cells[i+offs]['column']}
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
    @cached_result
    def columns_width(self):
        val = self._eval_parameter('columns_width', default=self.width, skip_type_convert=True)
        if isinstance(val, dict):
            # здесь хитрый способ распарсить словарь
            # - данный парамтер может быть только словарём
            # - ключ это число в виде строки, индекс колонки. можно указывать отрицательное значение (индекс с конца)
            # - значение это любой экспрешн но его результат должен быть числом
            return {int(k): int(self._eval_parameter_convert('', v, default=self.width)) for k, v in val.items()}
        return None

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

    def _adjust_columns_width(self, columns):
        custom_columns_width = self.columns_width
        if not custom_columns_width:
            return columns
        # общая ширина колонок
        full_columns_width = sum(columns.values())
        # заменяем отрицательные индексы на абсолютные
        _filtered = {}
        for c, val in custom_columns_width.items():
            if c < 0:
                if abs(c) > len(columns):
                    # слишком большой индекс
                    # del custom_columns_width[c]
                    continue
                # del custom_columns_width[c]
                # custom_columns_width[len(columns) + c] = val
                _filtered[len(columns) + c] = val
            else:
                if c > len(columns)-1:
                #     # слишком большой индекс
                #     del custom_columns_width[c]
                    continue
                _filtered[c] = val
        custom_columns_width = _filtered
        # ширина колонок с неограниченным размером
        free_size_columns = [x for x in range(len(columns)) if
                             x not in custom_columns_width]  # колонки у которых не фиксировали размер
        if free_size_columns:
            # неограниченные колонки делят оставшуюся ширину поровну
            fixed_size = sum(custom_columns_width.values())
            free_size = full_columns_width - fixed_size
            free_columns_width = free_size / len(free_size_columns)
        else:
            free_columns_width = 0
        # обнолвяем ширину колонок в списке
        for i in range(len(columns)):
            if i in custom_columns_width:
                columns[i] = max([1,custom_columns_width[i]])
            else:
                columns[i] = max([1, free_columns_width])
        return columns

    # def _adjust_columns_width__(self):
    #     custom_columns_width = self.columns_width
    #     cells = [x.parent._data for x in self._shapes]
    #     h_space = self.horizontal_spacing
    #     # выносим ширину колонок в одельный список
    #     columns = list({x['column']: {'w': x['width'], 'x': x['x']} for x in cells}.values())
    #     # количество колонок
    #     full_columns_width = sum([x['w'] for x in columns])
    #
    #     # заменяем отрицательные индексы на абсолютные
    #     for c, val in custom_columns_width.items():
    #         if c < 0:
    #             del custom_columns_width[c]
    #             custom_columns_width[len(columns) + c] = val
    #
    #     free_size_columns = [x for x in range(len(columns)) if
    #                          x not in custom_columns_width]  # колонки у которых не фиксировали размер
    #     if free_size_columns:
    #         fixed_size = sum(custom_columns_width.values())
    #         free_size = full_columns_width - fixed_size
    #         free_columns_width = free_size / len(free_size_columns)
    #     else:
    #         free_columns_width = 0
    #     x_coord = 0
    #     for index, data in enumerate(columns):
    #         if index in custom_columns_width:
    #             data['w'] = custom_columns_width[index] - h_space//2
    #         else:
    #             data['w'] = free_columns_width - h_space//2
    #         if index > 0:
    #             data['x'] = x_coord + h_space + self.padding_left
    #
    #         else:
    #             data['x'] = x_coord + self.padding_left
    #         x_coord += data['w'] + h_space
    #
    #     columns = dict(enumerate(columns))
    #
    #     for cell in cells:
    #         cell['x'] = columns[cell['column']]['x']
    #         cell['width'] = columns[cell['column']]['w']
    #     for i in range(len(self._shapes)):
    #         self._shapes[i].parent._data.update(cells[i])

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
        one_cell_width = cells_width / columns  # ширина одной колонки в случае если все колонки одинаковы
        all_columns_width = {x: one_cell_width for x in range(columns)}
        # рассчёт индивидуальной ширины
        all_columns_width = self._adjust_columns_width(all_columns_width)
        # перерассчёт координат Х
        all_columns_x = {}
        curr = 0
        for col, w in all_columns_width.items():
            # здесь каждая колонка начинается после предыдущей. Отступы добавятся позже
            all_columns_x[col] = curr
            curr += w

        # общая высота, занимаемая строками
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
            col_width = all_columns_width[col]  #  ширина текущей колонки
            col_x = all_columns_x[col]          # координата Х
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

    def draw_shape(self, size, **kwargs):
        canvas = self._get_canvas(size)
        shapes = self.get_cell_shapes()
        if shapes:
            for shape in shapes:
                # if shape._local_context['row'] == 1:
                #     print(shape._data, shape.y, shape.y_draw)
                overlay = shape.render(size)
                canvas = Image.alpha_composite(canvas, overlay)
        return canvas
