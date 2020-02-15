from __future__ import absolute_import
from .base_shape import BaseShape, EmptyShape
from ..utils.exceptions import PresetError
from ..shape import get_shape_class
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
        self._shapes = self._create_shapes_from_data()

    def _create_shapes_from_data(self, **kwargs):
        if self.width == 0:
            logger.warning('Grid width is 0')
        if self.height == 0:
            logger.warning('Grid height is 0')
        shapes = []
        shape_list = self._data['shapes']
        cells = self.generate_cells(len(shape_list))
        for i, shape_config in enumerate(shape_list):
            if not shape_config:
                continue
            shape_type = shape_config.get('type')
            if shape_type is None:
                raise PresetError('Shape type not defined in template element: {}'.format(shape_config))
            cells[i]['parent'] = self
            shape_config['parent'] = EmptyShape(cells[i], self.context)
            shape_cls = get_shape_class(shape_type)
            shape = shape_cls(shape_config, self.context, **kwargs)
            shapes.append(shape)
            if shape.id is not None:
                if shape.id in self.scope:
                    raise PresetError('Duplicate shape ID: {}'.format(shape.id))
            self.add_shape(shape)
        return shapes

    @property
    def vertical_spacing(self):
        return self._eval_parameter('vertical_spacing', default=0)

    @property
    def horizontal_spacing(self):
        return self._eval_parameter('horizontal_spacing', default=0)

    @property
    def rows(self):
        return self._eval_parameter('rows', default='auto')

    @property
    def max_row_height(self):
        return self._eval_parameter('max_row_height', default=0)

    @property
    def max_column_width(self):
        return self._eval_parameter('max_column_width', default=0)

    @property
    def columns(self):
        return self._eval_parameter('columns', default='auto')

    def generate_cells(self, count, cols=None, rows=None):
        # todo: выравнивание неполных строк и колонок
        cells = []
        # рассчитываем количество строк и колонок
        columns = cols or self.columns
        rows = rows or self.rows
        if columns == 'auto' and rows == 'auto':
            columns = rows = count/2
        elif columns == 'auto':
            columns = count//rows
        elif rows == 'auto':
            rows = count//columns
        # общая ширина, занимаемая колонками
        cells_width = self.width - self.horizontal_spacing
        one_cell_width = cells_width // columns
        width_limit = self.max_column_width
        if width_limit:
            one_cell_width = min([one_cell_width, width_limit])
        # общая ширина, занимаемая строками
        cells_height = self.height - self.vertical_spacing
        one_cell_height = cells_height // rows
        height_limit = self.max_row_height
        if height_limit:
            one_cell_height = min([one_cell_height, height_limit])

        for i in range(count):
            cells.append(dict(
                x=(one_cell_width * (i % columns)) + self.horizontal_spacing,
                y=(one_cell_height*(i//columns)) + self.vertical_spacing,
                width=one_cell_width - self.horizontal_spacing,
                height=one_cell_height - self.vertical_spacing
            ))
        return cells

    def get_cell_shapes(self):
        return self._shapes

    def render(self, size, **kwargs):
        canvas = self._get_canvas(size)
        for shape in self.get_cell_shapes():
            overlay = shape.render(size)
            canvas = Image.alpha_composite(canvas, overlay)
        return canvas
