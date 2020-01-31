from __future__ import absolute_import
from weakref import ref
import re
from PIL.ImageDraw import ImageDraw


class AbstractShape(object):
    shape_name = None
    __instances__ = {}

    def __init__(self, shape_data, renderer, **kwargs):
        if shape_data.get('id') == 'parent':
            raise NameError('ID cannot be named as "parent"')
        self._data = shape_data
        self.renderer = ref(renderer)

        self._parent = DefaultParent(renderer)
        if 'parent' in shape_data:
            if shape_data['parent'] not in self.scope:
                raise RuntimeError('Parent object {} not found in scope. Maybe parent object not defined yet?')
            parent = self.scope[shape_data['parent']]
            from .rect import RectShape
            # if not issubclass(parent.__class__, (RectShape,)):
            #     raise TypeError('Parent object can`t be {}'.format(type(parent)))
            self._parent = parent

    def __repr__(self):
        return '<{} {}>'.format(self.__class__.__name__, self.id or 'no-id')

    def __str__(self):
        return '{} #{}'.format(self.__class__.__name__, self.id or 'none')

    @property
    def parent(self):
        return self._parent

    @property
    def id(self):
        return self._data.get('id')

    @property
    def context(self) -> dict:
        return self.renderer().variables

    @property
    def defaults(self):
        return self.renderer().defaults

    @property
    def render_variables(self):
        return dict(
            source_width=self.renderer().source.size[0],
            source_height=self.renderer().source.size[1]
        )

    @property
    def scope(self):
        return {k: v for k, v in self.renderer().scope.items() if k != self.id}

    @property
    def source_image(self):
        return self.renderer().source

    def _eval_parameter(self, key: str, default_key=None, **kwargs):
        """
        Получение значения параметра по имени из данных шейпы

        Parameters
        ----------
        key: str
        default_key: str
        """
        val = self._data.get(key)
        if val is None:
            val = self.defaults.get(default_key or key)
        if val is None:
            if 'default' in kwargs:
                return kwargs['default']
            raise KeyError(f'Key "{key}" not found')
        return self._eval_parameter_convert(key, val) or val

    def _eval_parameter_convert(self, key, val: str, **kwargs):
        """
        Получение реального значения параметра

        Parameters
        ----------
        key: str
        val: str
        default_key: str
        """
        # определение типа
        if isinstance(val, (int, float, list, tuple, dict)):
            return val
        if not isinstance(val, str):
            raise TypeError('Unsupported type {}'.format(type(val)))
        # остается только строка
        if val.isdigit():   # int
            return int(val)
        elif re.match(r"^\d*\.\d*$", val):  # float
            return float(val)
        # определение других вариантов
        for func in [self._eval_percent_of_default,
                     self._eval_from_scope,
                     self._eval_from_variables,
                     self._eval_expression]:
            res = func(key, val, **kwargs)
            if res is not None:
                return res

    def _eval_percent_of_default(self, key, val, **kwargs):
        """
        Вычисление процентного отношения от дефолного значения

        >>> {"size": "100%"}

        Parameters
        ----------
        key
        val
        default_key

        Returns
        -------

        """
        match = re.match(r'^(\d+)%$', val)
        if not match:
            return
        percent = float(match.group(1))
        default = kwargs.get('default_value', self.defaults.get(kwargs.get('default_key') or key))
        if default is None:
            raise KeyError('No default value for key {}'.format(key))
        if isinstance(percent, (float, int)):
            return (default/100)*percent
        else:
            raise TypeError('Percent value must be int or float, not {}'.format(type(percent)))

    def _eval_from_scope(self, key:str, val: str, **kwargs):
        """
        Обращение к значениям параметрам других шейп

            >>> {"x": "other_shape.x"}

        Parameters
        ----------
        key: str
        val: str
        default_key: str
        """
        match = re.match(r'^(\w+)\.(\w+)$', val)
        if not match:
            return
        name, attr = match.groups()
        if name == self.id:
            raise RecursionError('Don`t use ID of same object in itself expression. '
                                 'Use name "self": "x": "=-10-self.width.')
        if name == 'parent':
            return getattr(self.parent, attr)
        if name == 'self':
            return getattr(self, attr)
        if name not in self.scope:
            # raise ValueError('Name "{}" not exists'.format(name))
            return
        return getattr(self.scope[name], attr)

    def _eval_from_variables(self, key:str, val: str, **kwargs):
        """
        Получение значения из глобального контекста переменных

            >>> {"text_size": "$text_size" }

        Parameters
        ----------
        key: str
        val: str
        default_key: str
        """
        match = re.match(r"\$([\w\d_]+)", val)
        if not match:
            return
        variable = match.group(1)
        if variable in self.context:
            return self.context[variable]
        elif variable in self.defaults:
            return self.defaults[variable]
        elif variable in self.render_variables:
            return self.render_variables[variable]
        else:
            raise KeyError('No key "{}" in context or defaults'.format(variable))

    def _eval_expression(self, key: str, expr: str, **kwargs):
        """
        Выполнение экспрешена. Экспрешен должен бысть строкой, начинающийся со знака "="

            >>> {"width": "=other.x-$padding/2"}

        Parameters
        ----------
        key: str
        expr: str
        default_key: str
        """
        if not expr.startswith('='):
            return
        expr = expr.lstrip('=')
        for op in re.findall(r"[\w\d.%$]+", expr):
            val = self._eval_parameter_convert(key, op)
            if val is None:
                val = op
                # raise ValueError('Expression operand "{}" is nt correct: {}'.format(op, expr))
            expr = expr.replace(op, str(val if not callable(val) else val()))
        res = eval(expr)
        return res

    def render(self, img: ImageDraw, **kwargs):
        raise NotImplementedError


class DefaultParent:
    def __init__(self, renderer):
        self._renderer = ref(renderer)

    @property
    def _source(self):
        return self._renderer().source

    @property
    def x(self):
        return 0

    @property
    def y(self):
        return 0

    @property
    def width(self):
        return self._source.size[0]

    @property
    def height(self):
        return self._source.size[1]

    @property
    def size(self):
        return self._source.size


class BaseShape(AbstractShape):

    @property
    def color(self):
        return self._eval_parameter('color')

    @property
    def x(self):
        val = self._eval_parameter('x')
        if val < 0:
            return int(self.parent.x + self.parent.width + val)
        else:
            return int(self.parent.x + val)

    @property
    def y(self):
        val = self._eval_parameter('y')
        if val < 0:
            return int(self.parent.y + self.parent.height + val)
        else:
            return int(self.parent.y + val)
