from __future__ import absolute_import
from .base_shape import BaseShape, EmptyShape
from ..utils.exceptions import PresetError
from ..shape import get_shape_class


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
    def columns(self):
        return self._eval_parameter('columns', default='auto')

    def generate_cells(self, count, cols=None, rows=None):
        # todo: выравнивание неполных строк и колонок
        cells = []
        columns = cols or self.columns
        if columns == 'auto':
            # todo: compute auto value
            columns = count
        cells_width = self.width - self.horizontal_spacing
        one_cell_width = cells_width // columns

        rows = rows or self.rows
        if rows == 'auto':
            # todo: compute auto value
            rows = 1
        cells_height = self.height - self.vertical_spacing
        one_cell_height = cells_height // rows

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

    def render(self, img, **kwargs):
        for shape in self.get_cell_shapes():
            shape.render(img)
