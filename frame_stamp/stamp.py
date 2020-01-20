from __future__ import absolute_import
from .shape.base_shape import BaseShape
from PIL import Image, ImageDraw
from .shape import get_shape_class
from .utils.exceptions import PresetError
from .utils import exceptions


class FrameStamp(object):
    class FORMAT:
        JPG = "JPEG"
        PNG = "PNG"

    def __init__(self, preset, variables, **kwargs):
        self._preset = preset
        self.defaults = {}
        self.variables = variables
        self._shapes = []
        self._scope = {}
        self._source = None
        self._create_shapes_from_preset(**kwargs)

    def _create_shapes_from_preset(self, **kwargs):
        for shape_config in self.preset['shapes']:
            shape_type = shape_config.pop('type', None)
            if not shape_type:
                raise PresetError('Shape type not defined in preset element')
            shape_cls = get_shape_class(shape_type)     # type: BaseShape
            shape = shape_cls(shape_config, self, **kwargs)
            self.add_shape(shape)

    @property
    def scope(self):
        return self._scope

    @property
    def preset(self):
        """
        Текущий пресет с применёнными оверрайдами

        Returns
        -------
        dict
        """

        return self._preset

    def add_shape(self, shape, **kwargs):
        """
        Добавить новый айтем шейпы в набор

        Parameters
        ----------
        shape: BaseShape
        kwargs: dict

        Returns
        -------
        bool
        """
        if not isinstance(shape, BaseShape):
            raise TypeError('Shape bus be subclass of {}'.format(BaseShape.__name__))
        if shape.id is not None:
            if shape.id in self._scope:
                raise exceptions.PresetError('Duplicate shape ID: {}'.format(shape.id))
            self._scope[shape.id] = shape
        self._shapes.append(shape)

    def get_shapes(self):
        """
        Все имеющиеся шейпы

        Returns
        -------
        list
        """
        return self._shapes

    def set_source(self, draw):
        self._source = draw

    def render(self, input_path: str, output_path: str, context: dict, **kwargs):
        """
        Рендер всех шейп на кадре

        Parameters
        ----------
        input_path
        output_path
        context: dict
        kwargs

        Returns
        -------
        str
        """
        # формат файла
        frmt = self._get_output_format(output_path)
        # создание объекта Image
        img = Image.open(input_path)    # type: Image
        if frmt == self.FORMAT.PNG:
            img = img.convert('RGBA')
        # создание объекта Draw
        painter = ImageDraw.Draw(img)
        self.set_source(painter)
        # рисование всех шейп
        for shape in self.get_shapes():     # type: BaseShape
            shape.render(painter, **kwargs)
        img.save(output_path, frmt)
        return output_path

    def _get_output_format(self, path):
        return self.FORMAT.PNG
