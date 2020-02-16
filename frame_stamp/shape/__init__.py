from __future__ import absolute_import
import os
import inspect
from cgf_tools import load_module
from .base_shape import BaseShape

BASE_DIR = os.path.dirname(__file__)


def get_shape_class(name):
    if not name:
        raise ValueError('Shape name not set')
    if not isinstance(name, str):
        raise ValueError('Shape name must be string, not {}'.format(type(name)))
    for file in os.listdir(BASE_DIR):
        if file.startswith('_'):
            continue
        full_name = '.'.join([__name__, os.path.splitext(file)[0]])
        mod = load_module.load_from_dotted(full_name)
        # full_path = os.path.join(BASE_DIR, file)
        # mod = load_module.load_from_path(full_path, os.path.splitext(file)[0])
        for attr in dir(mod):
            cls = getattr(mod, attr)
            # if inspect.isclass(cls) and BaseShape in cls.__bases__:
            if inspect.isclass(cls) and issubclass(cls, BaseShape):
                if cls.shape_name == name:
                    return cls
    raise NameError('Shape name "{}" not found'.format(name))
