from .grid import GridShape


class RowShape(GridShape):
    """
    A special case forms a table. 1 row.

    Allowed parameters:
        columns        : column count
    """
    shape_name = 'row'

    def __init__(self, shape_data: dict, renderer, **kwargs):
        shape_data['rows'] = 1
        shape_data['columns'] = shape_data.get('columns') or len(shape_data.get('shapes', []))
        super(RowShape, self).__init__(shape_data, renderer, **kwargs)
