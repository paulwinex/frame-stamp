from __future__ import absolute_import
from .shape.base_shape import BaseShape
from PIL import Image, ImageDraw
from .shape import get_shape_class
from .utils.exceptions import PresetError
from .utils import exceptions
from pathlib import Path
import cgflogging

logger = cgflogging.getLogger(__name__)


class FrameStamp(object):
    class FORMAT:
        # должно совпадать со списокм форматов из Image.SAVE
        JPG = "JPEG"
        PNG = "PNG"

    def __init__(self, preset, variables, **kwargs):
        self._preset = preset
        self._variables = variables
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
    def variables(self):
        v = self._variables.copy()
        v.update(self.preset.get('vars', {}))
        return v

    @property
    def defaults(self):
        return self.preset.get('defaults', {})

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

    @property
    def source(self):
        return self._source

    def set_source(self, input_path):
        img = Image.open(input_path).convert('RGBA')  # type: Image
        self._source = img

    def render(self, output_path: str, **kwargs):
        """
        Рендер всех шейп на кадре

        Parameters
        ----------
        output_path
        kwargs

        Returns
        -------
        str
        """
        if not self.source:
            raise RuntimeError('Source image not set')
        # формат файла
        frmt = self._get_output_format(output_path)
        # создаём новый пустой слой по размеру исходника
        overlay = Image.new('RGBA', self.source.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        # рисование всех шейп на слое
        for shape in self.get_shapes():     # type: BaseShape
            logger.debug('Render shape %s', shape)
            # переменные для рендера берутся из словаря self.variables
            shape.render(draw, **kwargs)
        # склеивание исходника и слоя
        out = Image.alpha_composite(self.source, overlay)
        # сохраняем отрендеренный файл в формате RGB
        logger.debug('Save format %s to file %s', frmt, output_path)
        out.convert("RGB").save(output_path, frmt, quality=100)
        return output_path

    def _get_output_format(self, path):
        path = Path(path)
        if path.suffix.strip('.') == 'jpg':
            return self.FORMAT.JPG
        elif path.suffix.strip('.') == 'png':
            return self.FORMAT.PNG
