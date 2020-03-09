import re, os
from PIL.ImageDraw import ImageDraw, Image


class AbstractShape(object):
    """
    Абстрактная фигура.

        - Инициализация данных
        - Методы ресолвинга параметров
    """
    shape_name = None
    __instances__ = {}
    names_stop_list = ['parent']

    def __init__(self, shape_data, context, **kwargs):
        if shape_data.get('id') in self.names_stop_list:
            raise NameError('ID cannot be named as "parent"')
        self._data = shape_data
        self._parent = None
        self._context = context
        self._debug = bool(os.environ.get('DEBUG_SHAPES')) or self.variables.get('debug_shapes') or kwargs.get('debug_shapes')
        if 'parent' in shape_data:
            parent_name = shape_data['parent']
            if isinstance(parent_name, BaseShape):
                self._parent = parent_name
            else:
                parent_name = parent_name.split('.')[0]
                if parent_name not in self.scope:
                    raise RuntimeError('Parent object "{}" not found in scope. '
                                       'Maybe parent object not defined yet?'.format(parent_name))
                parent = self.scope[parent_name]
                self._parent = parent
        else:
            self._parent = RootParent(context, **kwargs)

    def __repr__(self):
        return '<{} {}>'.format(self.__class__.__name__, self.id or 'no-id')

    def __str__(self):
        return '{} #{}'.format(self.__class__.__name__, self.id or 'none')

    @property
    def parent(self):
        return self._parent

    @property
    def context(self):
        return self._context

    @property
    def id(self):
        return self._data.get('id')

    @property
    def variables(self) -> dict:
        return {
            "source_width": self.source_image.size[0],
            "source_height": self.source_image.size[1],
            **self.context['variables']
            }

    @property
    def defaults(self):
        return self.context['defaults']

    @property
    def scope(self):
        """
        Список всех зарегистрированных нод, исключая себя и ноды без ID

        Returns
        -------
        dict
        """
        return {k: v for k, v in self.context['scope'].items() if k != self.id}

    @property
    def source_image(self):
        return self.context['source_image']

    def add_shape(self, shape):
        return self.context['add_shape'](shape)

    def is_enabled(self):
        try:
            return self._eval_parameter('enabled', default=True)
        except KeyError:
            return False

    # expressions

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
            raise KeyError(f'Key "{key}" not found in defaults')
        resolved = self._eval_parameter_convert(key, val)
        return resolved if resolved is not None else val

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
        if isinstance(val, (int, float, list, tuple, dict, bool)):
            return val
        if not isinstance(val, str):
            raise TypeError('Unsupported type {}'.format(type(val)))
        # остается только строка
        if val.isdigit():  # int
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
        return val

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
        default = kwargs.get('default', self.defaults.get(kwargs.get('default_key') or key))
        if default is None:
            raise KeyError('No default value for key {}'.format(key))
        default = self._eval_parameter_convert(key, default)
        if isinstance(percent, (float, int)):
            return (default / 100) * percent
        else:
            raise TypeError('Percent value must be int or float, not {}'.format(type(percent)))

    def _eval_from_scope(self, key: str, val: str, **kwargs):
        """
        Обращение к значениям параметрам других шейп

            >>> {"x": "other_shape_id.x"}

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
            return
        return getattr(self.scope[name], attr)

    def _eval_from_variables(self, key: str, val: str, **kwargs):
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
        if variable in self.variables:
            return self._eval_parameter_convert(key, self.variables[variable])
        elif variable in self.defaults:
            return self.defaults[variable]
        else:
            raise KeyError('No key "{}" in variables or defaults'.format(variable))

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


class BaseShape(AbstractShape):
    """
    Базовая фигура.
     - Реализация системы координат
     - Цвет
     - Дебаг

    Allowed parameters:
        x                  : Координата Х
        y                  : Координата У
        color              : Цвет текста
        alight_h           : Выравнивание относительно координаты X (left, right, center)
        alight_v           : Выравнивание относительно координаты X (top, bottom, center)
        padding            : Выравнивание строк между собой для многострочного текста
        parent             : Родительский объект

    """
    default_width = 0
    default_height = 0

    # def __getattribute__(self, item):
    #     if item == 'render' and self._debug_render:
    #         orig = super(AbstractShape, self).__getattribute__(item)
    #
    #         def wrapper(size, **kwargs):
    #             rendered = orig(size, **kwargs)
    #             return self._render_debug(rendered, size)
    #         wrapper.__name__ = 'render'
    #         return wrapper
    #     else:
    #         return super().__getattribute__(item)

    def _render_debug(self, default_render, size):
        overlay = self._get_canvas(size)
        img = ImageDraw(overlay)
        img.line([
            (self.left, self.top),
            (self.right, self.top),
            (self.right, self.bottom),
            (self.left, self.bottom),
            (self.left, self.top)
        ], 'red', 1)

        img.line([
            (self.parent.left + 1, self.parent.top + 1),
            (self.parent.right - 1, self.parent.top + 1),
            (self.parent.right - 1, self.parent.bottom - 1),
            (self.parent.left + 1, self.parent.bottom - 1),
            (self.parent.left + 1, self.parent.top + 1)
        ], 'yellow', 1)
        return Image.alpha_composite(default_render, overlay)

    def _get_canvas(self, size):
        return Image.new('RGBA', size, (0, 0, 0, 0))

    def draw_shape(self, size, **kwargs):
        raise NotImplementedError

    def render(self, size, **kwargs):
        if not self.is_enabled():
            return self._get_canvas(size)
        result = self.draw_shape(size, **kwargs)
        if self._debug:
            result = self._render_debug(result, size)
        return result

    @property
    def x(self):
        val = self._eval_parameter('x', default=0)
        align = self.align_h
        if align == 'center':
            return int(self.parent.x + val + (self.parent.width/2) - (self.width / 2))
        elif align == 'right':
            return int(self.parent.x + val + self.parent.width - self.width)
        else:
            return int(self.parent.x + val)

    @property
    def y(self):
        val = self._eval_parameter('y', default=0)
        align = self.align_v
        if align == 'center':
            return int(self.parent.y + val + (self.parent.height/2) - (self.height / 2))
        elif align == 'bottom':
            return int(self.parent.y + val + self.parent.height - self.height)
        else:
            return int(self.parent.y + val)

    @property
    def x_draw(self):
        return self.x0 + self.padding_left

    @property
    def y_draw(self):
        return self.y0 + self.padding_top

    @property
    def width_draw(self):
        return self.x1 - self.padding_right

    @property
    def height_draw(self):
        return self.y1 - self.padding_bottom

    @property
    def top(self):
        return self.y0

    @property
    def left(self):
        return self.x0

    @property
    def bottom(self):
        return self.y1

    @property
    def right(self):
        return self.x1

    @property
    def x0(self):
        return self.x

    @property
    def x1(self):
        return self.x0 + self.width

    @property
    def y0(self):
        return self.y

    @property
    def y1(self):
        return self.y0 + self.height

    @property
    def width(self):
        return self._eval_parameter('width', default=self.default_width)

    @property
    def height(self):
        return self._eval_parameter('height', default=self.default_height)

    @property
    def align_v(self):
        return self._eval_parameter('align_v', default=None)

    @property
    def align_vertical(self):
        return self.align_v

    @property
    def align_h(self):
        return self._eval_parameter('align_h', default=None)

    @property
    def align_horizontal(self):
        return self.align_h

    @property
    def center(self):
        return (
            (self.x0 + self.x1) // 2,
            (self.y0 + self.y1) // 2
        )

    @property
    def padding(self):
        param = self._eval_parameter('padding', default=(0, 0, 0, 0))
        if not isinstance(param, (list, tuple)):
            raise TypeError('Padding parameter must be list or tuple')
        if len(param) != 4:
            raise ValueError('Padding parameter must be size = 4')
        return tuple(param)

    @property
    def padding_top(self):
        return self._eval_parameter('padding_top', default=None) or self.padding[0]

    @property
    def padding_right(self):
        return self._eval_parameter('padding_right', default=None) or self.padding[1]

    @property
    def padding_bottom(self):
        return self._eval_parameter('padding_bottom', default=None) or self.padding[2]

    @property
    def padding_left(self):
        return self._eval_parameter('padding_left', default=None) or self.padding[3]

    @property
    def color(self):
        clr = self._eval_parameter('color', default=(0, 0, 0, 255))
        if isinstance(clr, list):
            clr = tuple(clr)
        return clr


class EmptyShape(BaseShape):
    shape_name = 'empty'

    def render(self, img: ImageDraw, **kwargs):
        pass


class RootParent(BaseShape):
    def __init__(self, context, *args, **kwargs):
        self._context = context
        self._data = {}
        self._parent = None
        self._debug_render = False

    def render(self, *args, **kwargs):
        pass

    @property
    def x(self):
        return 0

    @property
    def y(self):
        return 0

    @property
    def width(self):
        return self.source_image.size[0]

    @property
    def height(self):
        return self.source_image.size[1]

    @property
    def padding_top(self):
        return 0

    @property
    def padding_right(self):
        return 0

    @property
    def padding_bottom(self):
        return 0

    @property
    def padding_left(self):
        return 0
