from __future__ import absolute_import
from weakref import ref
import re


class BaseShape(object):
    shape_name = None
    __instances__ = {}

    def __init__(self, shape_data, renderer, **kwargs):
        self._data = shape_data
        self.renderer = ref(renderer)   # type: FrameStamp

    def __repr__(self):
        return '<{} {}>'.format(self.__class__.__name__, self.id or 'no-id')

    def __str__(self):
        return self.__class__.__name__

    @property
    def id(self):
        return self._data.get('id')

    @property
    def context(self) -> dict:
        return self.renderer.variables

    @property
    def defaults(self):
        return self.renderer.defaults

    @property
    def scope(self):
        return {k: v for k, v in self.renderer.scope.items() if k != self.id}

    def _eval_parameter(self, key):
        val = self._data[key]
        if isinstance(val, (int, float)):
            return val
        res = self._eval_percent_of_default(key, val)
        if res is not None:
            return res
        return val

    def _eval_percent_of_default(self, key, val):
        match = re.match('(\d)+%', val)
        if not match:
            return
        percent = float(match.group(1))
        default = self.defaults.get(key)
        if default is None:
            raise KeyError('No default value for key {}'.format(key))
        if isinstance(percent, (float, int)):
            return (default/100)*percent
        else:
            raise TypeError('Percent value must be int or float, not {}'.format(type(percent)))

    def _eval_from_scope(self, val):
        match = re.match(r'(\w+)\.(\w+)', val)
        if not match:
            return
        name, attr = match.groups()
        if name not in self.scope:
            raise ValueError('Name "{}" not exists'.format(name))
        return getattr(self.scope[name], attr)



    def render(self, painter, **kwargs):
        pass

