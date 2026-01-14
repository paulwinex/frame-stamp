import math
import re, os
import string
import random

from PIL import Image, ImageDraw
import logging

from frame_stamp.utils import cached_result, geometry_tools
from frame_stamp.utils.point import Point
from frame_stamp.utils.rect import Rect

logger = logging.getLogger(__name__)


try:
    BICUBIC = Image.BICUBIC
except AttributeError:
    BICUBIC = Image.Resampling.BICUBIC


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
        return '{} #{}'.format(self.__class__.__name__, self.id or 'no-id')

    def clear_cache(self):
        self.__cache__.clear()

    def update_local_context(self, **kwargs):
        self._local_context.update(kwargs)

    @property
    @cached_result
    def parent(self):
        return self._parent or RootParent(self.context)

    def set_parent(self, parent):
        self._parent = parent

    @property
    @cached_result
    def context(self):
        return self._context

    @property
    def defaults(self):
        return self._context['defaults']

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
            "unt": self.unit,
            "pnt": self.point,
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
    @cached_result
    def z_index(self):
        parent_index = self._parent.z_index if self._parent else 0
        return parent_index + self._eval_parameter('z_index', default=0) # shape_data.get('z_index', 0)

    @property
    def scope(self) -> dict:
        """
        List of all registered nodes except self and nodes without ID
        """
        return {k: v for k, v in self.context['scope'].items() if k != self.id}

    @property
    def source_image(self):
        return self.context['source_image']

    @property
    def source_image_raw(self):
        return self.context['source_image_raw']

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
            try:
                res = func(key, val, **kwargs)
            except KeyError:
                continue
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

            >>> {"width": "=$other.x-$value/2"}

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
            logger.exception('Evaluate expression error in field {}/{}: {}'.format(self, key, expr))
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
        parent             : Parent object

    """
    default_width = 0
    default_height = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._debug_enabled = bool(os.environ.get('DEBUG_SHAPES'))
        self._debug_variables = {}

    @property
    @cached_result
    def debug_options(self):
        debug_options = {}
        variables_debug_options = self.variables.get('debug')
        if variables_debug_options is not None:
            assert isinstance(variables_debug_options, dict),  'Debug value must be a dict'
            debug_options.update(variables_debug_options)
        self_debug_options = self._eval_parameter('debug', default=None)
        if self_debug_options is not None:
            assert isinstance(self_debug_options, dict),  'Debug value must be a dict'
            debug_options.update(self_debug_options)
        debug_options.setdefault('enabled', bool(self._debug_enabled))
        debug_options.setdefault('color', 'yellow')
        debug_options.setdefault('width', 1)
        debug_options.setdefault('offset', 0)
        debug_options.setdefault('parent_color', 'red')
        debug_options.setdefault('parent_width', 1)
        debug_options.setdefault('parent_offset', 0)
        debug_options.setdefault('rotation_pivot', False)
        debug_options.setdefault('rotation_pivot_color', 'green')
        debug_options.setdefault('rotation_pivot_size', self.point*2)
        debug_options.setdefault('parent', False)
        debug_options.setdefault('canvas', False)
        debug_options.setdefault('canvas_color', 'blue')
        debug_options.setdefault('canvas_width', 1)
        return debug_options

    @property
    def debug(self):
        return self.debug_options['enabled']

    def _render_debug(self, canvas):
        drw = ImageDraw.Draw(canvas)
        w, h = canvas.size
        zp = self._debug_variables.get('zero_point', Point(0, 0))
        debug_rect = Rect(zp.x, zp.y, self.width, self.height)
        points = [geometry_tools.rotate_point_around_point(pt, debug_rect.center, -self.global_rotate) for pt in debug_rect.line(as_tuple=True)]
        drw.line(points, fill=self.debug_options['color'], width=self.debug_options['width'])
        if self.debug_options.get('canvas'):
            drw.line([
                (1+self.debug_options['offset'], 1+self.debug_options['offset']),
                (w - 1-self.debug_options['offset'], 1+self.debug_options['offset']),
                (w - 1-self.debug_options['offset'], h - 1-self.debug_options['offset']),
                (1+self.debug_options['offset'], h - 1-self.debug_options['offset']),
                (1+self.debug_options['offset'], 1+self.debug_options['offset'])
            ], self.debug_options['canvas_color'], self.debug_options['canvas_width'])
        return drw

    def _render_debug_pivot(self):
        draw_size = int(self.debug_options['rotation_pivot_size'])
        if draw_size:
            pivot_image = Image.new('RGBA', (draw_size, draw_size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(pivot_image)
            draw.ellipse(
                (0, 0, draw_size, draw_size),
                fill=self.debug_options['rotation_pivot_color'],
                outline=None,
                width=1)
            return pivot_image

    def _render_debug_parent(self, size, shape_canvas, paste_pos, **kwargs):
        color = self.debug_options.get('parent_color', 'orange')
        width = self.debug_options.get('parent_width', 1)
        offset = self.debug_options.get('parent_offset', 0)
        canvas = self._get_canvas(size)
        drw = ImageDraw.Draw(canvas)
        rect = Rect(self.parent.x-offset,
                    self.parent.y-offset,
                    self.parent.width-1+(offset*2),
                    self.parent.height-1+(offset*2))
        drw.line(rect.line(), color, width)
        return canvas, (0,0 )

    def _get_canvas(self, size):
        return Image.new('RGBA', size, (0, 0, 0, 0))

    @property
    def raw_rect(self):
        return Rect(self.x,self.y, self.width, self.height)

    @property
    def raw_bound(self):
        return self.raw_rect.points()

    @property
    def rotated_rect(self):
        return self.raw_rect.rotate(self.global_rotate, self.raw_rect.center)

    def _get_render_sized_canvas(self):
        side_size = int(self._compute_maximum_distance_from_center() * 2.2) + int(self.shape_canvas_offset()+2)
        canvas_size = (side_size, side_size)
        center = Point(side_size/2, side_size/2)
        zero = Point((side_size-self.width) / 2, (side_size-self.height) / 2)
        return self._get_canvas(canvas_size), canvas_size, center, zero

    def shape_canvas_offset(self):
        return 0

    def _compute_maximum_distance_from_center(self):
        return (self.width ** 2 + self.height ** 2) ** 0.5 / 2

    def draw_shape(self, shape_canvas: Image.Image, canvas_size: tuple, center: Point, zero_point: Point, **kwargs):
        raise NotImplementedError

    def _draw_gradient(self, image, gradient: dict):
        from ..utils.image_tools import get_gradient_renderer, mix_alpha_channels
        # todo: need to optimize!
        render = get_gradient_renderer(gradient['type'])
        grad_img = render(size=(self.width, self.height), **gradient)
        grad_canvas = Image.new('RGBA', image.size)
        grad_canvas.paste(grad_img, self._debug_variables['zero_point'].int().tuple)
        if gradient.get('use_gradient_alpha'):
            # copy alpha
            grad_alpha = grad_canvas.split()[-1].copy()
        mix_alpha_channels(image, grad_canvas)
        if gradient.get('use_gradient_alpha'):
            # apply copied alpha
            mix_alpha_channels(grad_alpha, image)
        image.alpha_composite(grad_canvas)

    def compute_rotation_offset(self):
        x = y = 0
        if self.rotate and self.rotation_offset:
            points = [self.rotation_transform(pt) for pt in self.raw_bound]
            if self.align_h == 'right':
                max_x  = max([pt.x for pt in points])
                x = max(0, max_x - self.parent.right)
            elif self.align_h == 'left':
                min_x = min([pt.x for pt in points])
                x = min(0, min_x - self.parent.x)
            if self.align_v == 'bottom':
                max_y = max([pt.y for pt in points])
                y = max(0, max_y - self.parent.bottom)
            elif self.align_v == 'top':
                min_y = min([pt.y for pt in points])
                y = -max(0, self.parent.top - min_y)
        return Point(x, y)

    def render(self, size, **kwargs):
        if not self.is_enabled():
            return self._get_canvas(size)
        # get current shape canvas size including rotation
        shape_canvas, canvas_size, center, zero_point = self._get_render_sized_canvas()
        self._debug_variables['zero_point'] = zero_point
        # draw base shape
        shape_canvas = self.draw_shape(shape_canvas, canvas_size, center, zero_point) or shape_canvas
        # gradient
        if self.gradient:
            for grad in self.gradient:
                if grad['enabled']:
                    self._draw_gradient(shape_canvas, grad)
        if self.global_rotate:
            # rotate around center
            shape_canvas = shape_canvas.rotate(self.global_rotate, expand=False, center=(*center,), resample=BICUBIC)
        # compute coords for pasting
        global_pos = Point(self.x, self.y)
        paste_pos = global_pos - zero_point
        # compute transformation offset for rotated shape
        pivot = Point(self.rotation_pivot)
        paste_offset = self.center - self.rotation_transform(self.center) + self.compute_rotation_offset()
        # move rotated shape
        paste_pos -= paste_offset
        # self debug draw ##############################
        if self.debug:
            self._render_debug(shape_canvas)

        # return main image ###########################
        yield shape_canvas, paste_pos.int()
        # #################

        # external debug draw ##########################
        if self.debug:
            if self.debug_options['rotation_pivot']:
                pivot_image = self._render_debug_pivot()
                if pivot_image:
                    yield pivot_image, (pivot-(pivot_image.size[0]/2)).int()
            if self.debug_options['parent']:
                parent_image, parent_paste_pos = self._render_debug_parent(size, shape_canvas, paste_pos, rotation_pivot=center, **kwargs)
                if parent_image:
                    yield parent_image, parent_paste_pos

    @property
    @cached_result
    def x(self):
        val = self._eval_parameter('x', default=0)
        if self.align_h == 'center':
            return int(self.parent.x + val + (self.parent.width/2) - (self.width / 2))
        elif self.align_h == 'right':
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
    def pos(self):
        return Point(self.x, self.y)

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
        return Point(
            self.center_x,
            self.center_y
        )

    @property
    @cached_result
    def center_x(self):
        return (self.x0 + self.x1) // 2

    @property
    @cached_result
    def center_y(self):
        return (self.y0 + self.y1) // 2

    @property
    def global_rotate(self):
        """Rotation including parents rotation"""
        return self.rotate + (self.parent.global_rotate if self.parent else 0)

    @property
    @cached_result
    def rotate(self):
        return self._eval_parameter('rotate', default=0)

    @property
    @cached_result
    def rotation_offset(self):
        return self._eval_parameter('rotation_offset', default=False)

    @property
    @cached_result
    def rotation_pivot(self):
        return Point(*self._eval_parameter('rotation_pivot', default=self.center))# + (self.parent.rotation_pivot if self.parent else 0)

    def rotation_transform(self, point, ind=0):
        point = Point(geometry_tools.rotate_point_around_point(point, self.rotation_pivot, -self.rotate))
        rotated_by_parents = self.parent.rotation_transform(point, ind+2)
        return rotated_by_parents

    @property
    @cached_result
    def color(self):
        clr = self._eval_parameter('color', default=(0, 0, 0, 255))
        if isinstance(clr, list):
            clr = tuple(clr)
        return clr

    @property
    @cached_result
    def gradient(self) -> dict:
        gradient = self._eval_parameter('gradient', default=None)
        if gradient is None:
            return None
        if isinstance(gradient, dict):
            gradient = [gradient]
        if not isinstance(gradient, list):
            raise TypeError('Gradient parameter must be dict, list of dict or None')
        gradient_list = []
        for grad in gradient:
            if not isinstance(grad, dict):
                raise TypeError('Gradient parameter must be dict, list of dict or None')
            if grad.get('type') not in ('linear', 'radial'):
                raise ValueError('Gradient type must be "linear" or "radial"')
            grad.setdefault('enabled', True)
            grad.setdefault('use_gradient_alpha', False)
            if grad.get('type') == 'linear':
                grad.setdefault('point1', (0, 0))
                grad.setdefault('point2', (0, 100))
                grad.setdefault('color1', (255, 255, 255, 255))
                grad.setdefault('color2', (0, 0, 0, 255))
            else:
                grad.setdefault('center', (50, 50))
                grad.setdefault('radius', 50)
                grad.setdefault('color1', (255, 255, 255, 255))
                grad.setdefault('color2', (0, 0, 0, 255))
            gradient_list.append(grad)
        return gradient_list

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
        return self._get_canvas(size) # TODO try size 1x1


class RootParent(BaseShape):
    def __init__(self, context, *args, **kwargs):
        self._context = context
        self._data = {}
        self._parent = None
        self._debug_render = False
        self.__cache__ = {}

    @property
    def z_index(self):
        return 0

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
    @cached_result
    def size(self):
        return self.width, self.height

    def rotation_transform(self, point, *args, **kwargs):
        return point

    @property
    def rotate(self):
        return 0

    @property
    def global_rotate(self):
        return 0
