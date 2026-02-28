from __future__ import absolute_import
import os
import inspect
from ..utils import load_from_dotted
from .base_shape import BaseShape
# import all shapes
from .rect import RectShape
from .circle import CircleShape
from .line import LineShape
from .polygon import PolygonShape
from .image import ImageShape
from .label import LabelShape
from .grid import GridShape
from .row import RowShape
from .column import ColumnShape
from .tile import TileShape

BASE_DIR = os.path.dirname(__file__)


def get_shape_class(name):
    for _, obj in globals().items():
        if inspect.isclass(obj) and issubclass(obj, BaseShape):
            if obj.shape_name == name:
                return obj


def __get_shape_class(name):
    """
    Старая версия для импорта по имени файла. не подходит для скомпиленного варианта
    """
    if not name:
        raise ValueError('Shape name not set')
    if not isinstance(name, str):
        raise ValueError('Shape name must be string, not {}'.format(type(name)))
    for file in os.listdir(BASE_DIR):
        if file.startswith('_'):
            continue
        full_name = '.'.join([__name__, os.path.splitext(file)[0]])
        mod = load_from_dotted(full_name)
        for attr in dir(mod):
            cls = getattr(mod, attr)
            if inspect.isclass(cls) and issubclass(cls, BaseShape):
                if cls.shape_name == name:
                    return cls
    raise NameError('Shape name "{}" not found'.format(name))
