import math
import re, os
import string
import random
from PIL.ImageDraw import ImageDraw
from PIL import Image
from frame_stamp.utils import cached_result
import logging

logger = logging.getLogger(__name__)


class AbstractShape(object):
    """
    Abstract shape.

    - Data initialization
    - Methods for resolving parameters

    Parameters
        id
        parent
        enabled
    """
    shape_name = None
    __instances__ = {}
    names_stop_list = ['parent']

    def __init__(self, shape_data, context, **kwargs):
        if shape_data.get('id') in self.names_stop_list:
            raise NameError('ID cannot be named as "parent"')
        self.__cache__ = {}
        self._data = shape_data
        self._parent = None
        self._context = context
        self._local_context = kwargs.get('local_context') or {}
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
        self.z_index = kwargs.get('z_index', 0) + shape_data.get('z_index', 0)

    def __repr__(self):
        return '<{} {}>'.format(self.__class__.__name__, self.id or 'no-id')

    def __str__(self):
        return '{} #{}'.format(self.__class__.__name__, self.id or 'none')

    def clear_cache(self):
        self.__cache__.clear()

    def update_local_context(self, **kwargs):
        self._local_context.update(kwargs)

    @property
    @cached_result
    def parent(self):
        return self._parent

    def set_parent(self, parent):
        self._parent = parent

    @property
    @cached_result
    def context(self):
        return self._context

    @property
    @cached_result
    def id(self):
        return self._data.get('id')

    @property
    @cached_result
    def skip(self):
        return self._eval_parameter('skip', default=False)

    @property
    @cached_result
    def variables(self) -> dict:
        return {
            "source_width": self.source_image.size[0],
            "source_height": self.source_image.size[1],
            "source_aspect": self.source_image.size[1]/self.source_image.size[0],
            "unit": self.unit,
            **self.context['variables'],
            **self._local_context
            }

    @property
    @cached_result
    def unit(self):
        # 1% from height
        return round(self.source_image.size[1]*0.01, 3)

    @property
    @cached_result
    def point(self):
        # relative almost monotonic size for any aspect and size
        from math import sqrt
        w, h = self.source_image.size
        return round(0.01*sqrt(w*h), 3)

    @property
    def defaults(self):
        return self.context['defaults']

    @property
    def scope(self) -> dict:
        """
        List of all registered nodes except self and nodes without ID
        """
        return {k: v for k, v in self.context['scope'].items() if k != self.id}

    @property
    def source_image(self):
        return self.context['source_image']

    def add_shape(self, shape):
        return self.context['add_shape'](shape)

    @cached_result
    def is_enabled(self):
        try:
            return self._eval_parameter('enabled', default=True)
        except KeyError:
            return False

    # expressions

    def _eval_parameter(self, key: str, default_key: str = None, **kwargs):
        """
        Receive value of parameter by name from shape data
        """
        val = self._data.get(key)
        if val is None:
            val = self.defaults.get(default_key or key)
        if val is None:
            if 'default' in kwargs:
                return kwargs['default']
            raise KeyError(f'Key "{key}" not found in defaults')
        resolved = self._eval_parameter_convert(key, val, **kwargs)
        return resolved if resolved is not None else val

    def _eval_parameter_convert(self, key, val: str, **kwargs):
        """
        Getting the real value of a parameter

        Parameters
        ----------
        key: str
        val: str
        default_key: str
        """
        # type definition
        if isinstance(val, (int, float, bool)):
            return val
        elif isinstance(val, (list, tuple)):
            return [self._eval_parameter_convert(key, x) for x in val]
        elif isinstance(val, dict):
            if not kwargs.get('skip_type_convert'):
                return {k: self._eval_parameter_convert(key, v, **kwargs) for k, v in val.items()}
            else:
                return val
        if not isinstance(val, str):
            raise TypeError('Unsupported type {}'.format(type(val)))
        # only the line remains
        if val.isdigit():  # int
            return int(val)
        elif re.match(r"^\d*\.\d*$", val):  # float
            return float(val)
        # unit
        if re.match(r"-?[\d.]+u", val):
            return float(val.rstrip('u')) * self.unit
        # point
        if re.match(r"-?[\d.]+p", val):
            return float(val.rstrip('p')) * self.point

        # identifying other options
        for func in [self._eval_percent_of_default,     # percentage of default value
                     self._eval_from_scope,             # data from another shape
                     self._eval_from_variables,         # data from template variables or from defaults
                     self._eval_expression]:            # execution of express
            res = func(key, val, **kwargs)
            if res is not None:
                return res
        return val

    def _eval_percent_of_default(self, key, val, **kwargs):
        """
        Calculating the percentage of the default value

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
        Accessing parameter values of other shapes

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
        Getting a value from the global variable context

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
            return self._eval_parameter_convert(key, self.defaults[variable])
        else:
            raise KeyError('No key "{}" in variables or defaults'.format(variable))

    def _eval_expression(self, key: str, expr: str, **kwargs):
        """
        Executing an expression. The expression must be a string starting with the "=" sign.

            >>> {"width": "=$other.x-$padding/2"}

        Parameters
        ----------
        key: str
        expr: str
        default_key: str
        """
        expr = expr.strip('`')
        if not expr.startswith('='):
            return
        expr = expr.lstrip('=')
        for op in re.findall(r"[\w\d.%$]+", expr):
            val = self._eval_parameter_convert(key, op)
            if val is None:
                val = op
                # raise ValueError('Expression operand "{}" is nt correct: {}'.format(op, expr))
            expr = expr.replace(op, str(val if not callable(val) else val()))
        try:
            res = eval(expr, {**locals(), **self.render_globals()})
        except Exception as e:
            logger.exception('Evaluate expression error: {}'.format(expr))
            raise
        return res

    def render_globals(self):
        return dict(
                random=random.random,
                uniform=random.uniform,
                randint=random.randint,
                random_seed=random.seed,
                math=math
            )

    def _render_variables(self, text, context):
        for pattern, name, _slice in re.findall(r"(\$([\w_]+)(\[[\d:]+])?)", text):
            val = context[name]
            if _slice:
                indexes = _slice.strip('[]').split(':')
                if not all((x.isdigit() for x in indexes)):
                    raise Exception(f'Invalid slice: {_slice}')
                if len(indexes) == 1:
                    val = val[int(indexes[0])]
                else:
                    val = val[slice(*[int(x) for x in indexes])]
            text = text.replace(pattern, str(val))
        return text


class BaseShape(AbstractShape):
    """
    Base Shape.
    - Coordinate system implementation
    - Color
    - Debug

    Allowed parameters:
        x                  : X coordinate
        y                  : Y coordinate
        color              : Text color
        alight_h           : Alignment relative to the X coordinate (left, right, center)
        alight_v           : Alignment relative to the Y coordinate (top, bottom, center)
        padding            : Line spacing for multi-line text
        parent             : Parent object

    """
    default_width = 0
    default_height = 0

    @property
    @cached_result
    def _debug_parent_offset(self):
        """Offset of parent outline relative to object outline"""
        return self._eval_parameter('debug_parent_offset', default=1)

    @property
    @cached_result
    def _debug_self_offset(self):
        """Offset of parent outline relative to object outline"""
        return self._eval_parameter('debug_self_offset', default=0)

    def _render_debug(self, default_render, size):
        overlay = self._get_canvas(size)
        img = ImageDraw(overlay)
        self_ofs = self._debug_self_offset
        debug_border_color = self._data.get('debug_border_color', 'red')
        if isinstance(debug_border_color, list):
            debug_border_color = tuple(debug_border_color)
        debug_border_width = self._data.get('debug_border_width', 1)
        img.line([
            (self.left + self_ofs, self.top + self_ofs),
            (self.right - self_ofs, self.top + self_ofs),
            (self.right - self_ofs, self.bottom - self_ofs),
            (self.left + self_ofs, self.bottom - self_ofs),
            (self.left + self_ofs, self.top + self_ofs)
        ], debug_border_color, debug_border_width)

        par_offset = self._debug_parent_offset
        debug_parent_border_color = self._data.get('debug_parent_border_color', 'yellow')
        if isinstance(debug_parent_border_color, list):
            debug_parent_border_color = tuple(debug_parent_border_color)
        debug_parent_border_width = self._data.get('debug_parent_border_width', 1)
        img.line([
            (self.parent.left + par_offset, self.parent.top + par_offset),
            (self.parent.right - par_offset, self.parent.top + par_offset),
            (self.parent.right - par_offset, self.parent.bottom - par_offset),
            (self.parent.left + par_offset, self.parent.bottom - par_offset),
            (self.parent.left + par_offset, self.parent.top + par_offset)
        ], debug_parent_border_color, debug_parent_border_width)
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
        result = self._apply_rotate(result)
        return result

    def _apply_rotate(self, img):
        if self.rotate:
            img = img.rotate(self.rotate, expand=False, center=self.rotate_pivot, resample=Image.BICUBIC)
        par = self.parent
        while par:
            if par.rotate:
                img = img.rotate(par.rotate, expand=False, center=par.rotate_pivot, resample=Image.BICUBIC)
            par = par.parent
        return img

    @property
    @cached_result
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
    @cached_result
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
    @cached_result
    def width(self):
        return int(self._eval_parameter('width', default=None) or self._eval_parameter('w', default=self.default_width))

    @property
    def w(self):
        return self.width

    @property
    @cached_result
    def height(self):
        return int(self._eval_parameter('height', default=None) or self._eval_parameter('h', default=self.default_height))

    @property
    def h(self):
        return self.height

    @property
    @cached_result
    def align_v(self):
        return self._eval_parameter('align_v', default=None)

    @property
    def align_vertical(self):
        return self.align_v

    @property
    @cached_result
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
    @cached_result
    def rotate(self):
        return self._eval_parameter('rotate', default=0)# + (self.parent.rotate if self.parent else 0)

    @property
    @cached_result
    def rotate_pivot(self):
        return self._eval_parameter('rotate_pivot', default=self.center)

    @property
    @cached_result
    def padding(self):
        param = self._eval_parameter('padding', default=(0, 0, 0, 0))
        if not isinstance(param, (list, tuple)):
            raise TypeError('Padding parameter must be list or tuple')
        if len(param) != 4:
            raise ValueError('Padding parameter must be size = 4')
        return tuple(map(int, param))

    @property
    @cached_result
    def padding_top(self):
        return int(self._eval_parameter('padding_top', default=None) or self.padding[0])

    @property
    @cached_result
    def padding_right(self):
        return int(self._eval_parameter('padding_right', default=None) or self.padding[1])

    @property
    @cached_result
    def padding_bottom(self):
        return int(self._eval_parameter('padding_bottom', default=None) or self.padding[2])

    @property
    @cached_result
    def padding_left(self):
        return int(self._eval_parameter('padding_left', default=None) or self.padding[3])

    @property
    @cached_result
    def color(self):
        clr = self._eval_parameter('color', default=(0, 0, 0, 255))
        if isinstance(clr, list):
            clr = tuple(clr)
        return clr

    def get_resource_search_dirs(self):
        paths = self.variables.get('local_resource_paths') or []
        paths.extend(self.defaults.get('local_resource_paths') or [])
        paths.append(os.path.abspath(os.path.dirname(__file__)+'/../fonts'))
        search_dirs_from_env = os.getenv('FRAMESTAMP_RESOURCE_DIR')
        if search_dirs_from_env:
            paths.extend(search_dirs_from_env.split(os.pathsep))
        return paths

    def get_resource_file(self, file_name):
        while '$' in file_name:
            file_name = string.Template(file_name).substitute({**self.variables, **self.defaults})
        file_name = os.path.expanduser(file_name)
        if os.path.isabs(file_name) and os.path.exists(file_name):
            return file_name
        else:
            for search_dir in self.get_resource_search_dirs():
                path = os.path.join(search_dir, file_name)
                if os.path.exists(path):
                    return path
            func = self.context['variables'].get('get_resource_func')
            if func:
                return func(file_name)


class EmptyShape(BaseShape):
    shape_name = 'empty'

    def draw_shape(self, size, **kwargs):
        return self._get_canvas(size)


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
    @cached_result
    def width(self):
        return self.source_image.size[0]

    @property
    @cached_result
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
