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

    def __init__(self, image, template, variables, **kwargs):
        self._template = template
        self._variables = variables
        self._shapes = []
        self._scope = {}
        self._source = None
        self._shared_context = dict(
            variables=self.variables,           # переменные для рендеринга
            source_image=self._source,          # исходная картинка. Для получения размера и других данных
            defaults=self.defaults,             # дефолтные значения из шаблона
            scope=self._scope,                  # список всех доступных шейп. Нужен для обращения к полям других шейп
            add_shape=self._add_shape_to_scope  # ссылка на функцию добавления шейпы, это нужно для составных шейп
        )
        self.set_source(image)
        self._create_shapes_from_template(**kwargs)

    def _create_shapes_from_template(self, **kwargs):
        for shape_config in self.template['shapes']:
            shape_type = shape_config.get('type')
            if shape_type is None:
                raise PresetError('Shape type not defined in template element: {}'.format(shape_config))
            shape_cls = get_shape_class(shape_type)
            if not shape_cls:
                raise TypeError(f'Shape type {shape_type} not found')
            shape = shape_cls(shape_config, self._shared_context, **kwargs)
            # if shape.is_enabled():
            self.add_shape(shape)
            # else:
            #     del shape

    @property
    def variables(self):
        v = self._variables.copy()
        v.update(self.template.get('variables', {}))
        return v

    @property
    def defaults(self):
        return self.template.get('defaults', {})

    @property
    def scope(self):
        return self._scope

    @property
    def template(self):
        """
        Текущий шаблон с применёнными оверрайдами

        Returns
        -------
        dict
        """
        return self._template

    def add_shape(self, shape):
        """
        Добавить новый айтем шейпы в набор

        Parameters
        ----------
        shape: BaseShape

        Returns
        -------
        bool
        """
        if not isinstance(shape, BaseShape):
            raise TypeError('Shape bus be subclass of {}'.format(BaseShape.__name__))
        self._add_shape_to_scope(shape)
        self._shapes.append(shape)

    def _add_shape_to_scope(self, shape):
        if shape.id is not None:
            if shape.id in self._scope:
                raise exceptions.PresetError('Duplicate shape ID: {}'.format(shape.id))
            self._scope[shape.id] = shape

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

    def set_source(self, input_image):
        if Image.isImageType(input_image):
            self._source = input_image.convert('RGBA')  # type: Image.Image
        elif isinstance(input_image, str):
            self._source = Image.open(input_image).convert('RGBA')  # type: Image.Image
        self._shared_context['source_image'] = self._source

    def render(self, input_image: str=None, save_path: str=None, **kwargs) -> Image.Image:
        """
        Рендер всех шейп на кадре

        Parameters
        ----------
        input_image
        save_path
        kwargs

        Returns
        -------
        Image.Image
        """
        if input_image:
            self.set_source(input_image)
        if not self.source:
            raise RuntimeError('Source image not set')
        # logger.debug(f'Start stamping with template "{self.template["name"]}"')
        # формат файла
        img_size = self.source.size
        for shape in self.get_shapes():     # type: BaseShape
            # создаём новый пустой слой по размеру исходника
            overlay = shape.render(img_size, **kwargs)
            self._source = Image.alpha_composite(self.source, overlay)

        if save_path:
            # сохраняем отрендеренный файл в формате RGB
            frmt = self._get_output_format(save_path)
            logger.debug('Save format %s to file %s', frmt, save_path)
            self._source.convert("RGB").save(save_path, frmt, quality=100)
        return self._source

    def _get_output_format(self, path):
        path = Path(path)
        if path.suffix.strip('.') == 'jpg':
            return self.FORMAT.JPG
        elif path.suffix.strip('.') == 'png':
            return self.FORMAT.PNG
