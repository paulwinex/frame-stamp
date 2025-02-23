from __future__ import absolute_import
from .shape import base_shape
from PIL import Image, ImageDraw, ImageFile
from .shape import get_shape_class
from .utils.exceptions import PresetError
from .utils import exceptions
from pathlib import Path
import logging

ImageFile.LOAD_TRUNCATED_IMAGES = True
logger = logging.getLogger(__name__)


class FrameStamp(object):
    class FORMAT:
        # must be matched with list of formats from Image.SAVE
        JPG = "JPEG"
        PNG = "PNG"

    def __init__(self, image, template, variables, **kwargs):
        self._template = template
        self._variables = variables or {}
        self._shapes = []
        self._scope = {}
        self._source = None
        self._shared_context = dict(
            variables=self.variables,           # variables for rendering
            source_image=self._source,          # source image. For getting original size and other parameters
            source_image_raw=self._source,              # source image raw data
            source_image_path=None,             # source image path
            defaults=self.defaults,             # default values from template
            scope=self._scope,                  # list of all available shapes. Needed for queries from other shapes
            add_shape=self._add_shape_to_scope  # reference to function to add shapes, needed for combined shapes
        )
        self.set_source(image)
        if self._source is None:
            raise PresetError('Source image not set')
        self._create_shapes_from_template(**kwargs)

    def _create_shapes_from_template(self, **kwargs):
        for i, shape_config in enumerate(self.template['shapes']):
            shape_type = shape_config.get('type')
            if shape_type is None:
                raise PresetError('Shape type not defined in template element: {}'.format(shape_config))
            shape_cls = get_shape_class(shape_type)
            if not shape_cls:
                raise TypeError(f'Shape type "{shape_type}" not found')
            shape = shape_cls(shape_config, self._shared_context, z_index=i, **kwargs)
            self.add_shape(shape)

    @property
    def variables(self):
        v = self.template.get('variables', {}).copy()
        v.update(self._variables)
        return v

    @property
    def defaults(self):
        return self.template.get('defaults', {})

    @property
    def scope(self):
        return self._scope

    @property
    def template(self) -> dict:
        """
        Current template with overrides
        """
        return self._template

    def add_shape(self, shape: base_shape.BaseShape):
        """
        Add a new shape item to a set
        """
        if not isinstance(shape, base_shape.BaseShape):
            raise TypeError('Shape bus be subclass of {}'.format(base_shape.BaseShape.__name__))
        self._add_shape_to_scope(shape)
        self._shapes.append(shape)

    def _add_shape_to_scope(self, shape):
        if shape.id is not None:
            if shape.id in self._scope:
                raise exceptions.PresetError('Duplicate shape ID: {}'.format(shape.id))
            self._scope[shape.id] = shape

    def get_shapes(self) -> list:
        """
        All shapes
        """
        return (x[1] for x in sorted(enumerate(self._shapes), key=lambda item: (item[1].z_index, item[0])))

    @property
    def source(self):
        return self._source

    def set_source(self, input_image):
        if Image.isImageType(input_image):
            self._source = input_image.convert('RGBA')  # type: Image.Image
            self._shared_context['source_image_raw'] = input_image.convert('RGBA')
        elif isinstance(input_image, (str, Path)):
            self._source = Image.open(input_image).convert('RGB').convert('RGBA')  # type: Image.Image
            self._shared_context['source_image_raw'] = Image.open(input_image).convert('RGB').convert('RGBA')
        else:
            raise TypeError('Source image must be string or PIL.Image')
        self._shared_context['source_image'] = self._source

    def render(self, input_image: str = None, save_path: str = None, **kwargs) -> Image.Image:
        """
        Render all shapes
        """
        if input_image:
            self.set_source(input_image)
        if not self.source:
            raise RuntimeError('Source image not set')
        img_size = self.source.size
        for shape in self.get_shapes():     # type: BaseShape
            if shape.skip:
                continue
            try:
                for overlay, pos in shape.render(img_size, **kwargs):
                    self._source.paste(overlay, tuple(pos), overlay)
                    del overlay
            except Exception as e:
                logger.error('Error rendering shape %s: %s', shape, e)
                raise
        if save_path:
            # save rendered file to RGB
            frmt = self._get_output_format(save_path)
            logger.debug('Save format %s to file %s', frmt, save_path)
            self._source.convert("RGB").save(save_path, frmt, quality=100)
        return self._source

    def _get_output_format(self, path: str):
        path = Path(path)
        if path.suffix.strip('.').lower() == 'jpg':
            return self.FORMAT.JPG
        elif path.suffix.strip('.').lower() == 'png':
            return self.FORMAT.PNG
