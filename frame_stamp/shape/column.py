from .grid import GridShape


class RowShape(GridShape):
    """
    Частный случай формы таблицы. 1 колонка.

    Allowed parameters:
        rows        : Количество строк
    """
    shape_name = 'column'

    def __init__(self, shape_data, renderer, **kwargs):
        shape_data['columns'] = 1
        shape_data['rows'] = len(shape_data.get('shapes')) or 0
        super(RowShape, self).__init__(shape_data, renderer, **kwargs)
