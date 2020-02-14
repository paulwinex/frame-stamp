from .grid import GridShape


class RowShape(GridShape):
    """
    Частный случай формы таблицы. 1 строка.

    Allowed parameters:
        columns        : Количество колонок
    """
    shape_name = 'row'

    def __init__(self, shape_data, renderer, **kwargs):
        shape_data['rows'] = 1
        shape_data['columns'] = len(shape_data.get('shapes')) or 0
        super(RowShape, self).__init__(shape_data, renderer, **kwargs)
