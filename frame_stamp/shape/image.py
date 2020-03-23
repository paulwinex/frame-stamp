from __future__ import absolute_import
from PIL import Image, ImageChops
from .base_shape import BaseShape
from pathlib import Path
import string
from ..utils import cached_result


class ImageShape(BaseShape):
    """
    Картинка

    Allowed parameters:
        source          : путь к исходному файлу
        transparency    : прозрчность (0-1)
        keep_aspect     : сохранять пропорции при изменении размера
        mask            : чёрно-белая маска
    """
    shape_name = 'image'

    def _get_image(self, value):
        """
        Чтение файла с диска

        Parameters
        ----------
        value: str

        Returns
        -------
        Image.Image
        """
        if value == '$source':  # исходная картинка кадра, не путать с source самой шейпы
            # возвращаем исходник кадра
            return self.source_image.copy()
        while '$' in value:
            value = string.Template(value).substitute(**self.variables)
        path = Path(value).expanduser().resolve()
        if not path.exists():
            raise IOError(f'Path not exists: {path.as_posix()}')
        return Image.open(path.as_posix())

    @property
    @cached_result
    def source(self):
        """
        Исходник картинки для рисования

        Returns
        -------
        Image.Image
        """
        if '_saved_source' not in self.__dict__:
            source = self._data.get('source')
            if not source:
                raise RuntimeError('Image source not set')
            img = self._get_image(source)
            # применение прозрачности и маски
            img = self.apply_mask(img, self.mask, self.transparency)
            # ресайз
            if not self.size == img.size:
                target_size = list(self.size)
                if target_size[0] == 0:
                    target_size[0] = img.size[0]
                if target_size[1] == 0:
                    target_size[1] = img.size[1]
                if self.keep_aspect:
                    img.thumbnail(target_size, Image.ANTIALIAS)
                else:
                    img = img.resize(target_size, Image.ANTIALIAS)

            self.__dict__['_saved_source'] = img.convert('RGBA')
        return self.__dict__['_saved_source']

    @property
    @cached_result
    def size(self):
        src = getattr(self, '_saved_source', None)
        if src:
            return src.size
        return (self.width, self.height)

    @property
    @cached_result
    def mask(self):
        mask = self._data.get('mask')
        if not mask:
            return
        img = self._get_image(mask)
        return img.convert('L')

    def apply_mask(self, img, mask, transparency=0):
        # get source
        if not Image.isImageType(img):
            img = Image.open(img).convert('RGBA')
        else:
            img = img.convert('RGBA')
        # extract original alpha
        alpha = img.split()[-1]
        # create clean image for new alpha
        im_alpha = Image.new("RGBA", img.size, (0, 0, 0, 255))
        # insert alpha with mask
        im_alpha.paste(alpha, mask=alpha)
        im_alpha = im_alpha.convert('L')
        if transparency > 0:
            # apply transparency
            transp = Image.new("L", img.size, min(max(int(255 * (1 - self.transparency)), 0), 255))
            im_alpha = ImageChops.multiply(im_alpha, transp)
        if mask:
            # apply mask
            if not Image.isImageType(mask):
                mask = Image.open(mask).convert('L')
            else:
                mask = mask.convert('L')
            # multiply original alpha and mask
            im_alpha = ImageChops.multiply(im_alpha, mask)
        # put alpha to image
        img.putalpha(im_alpha.convert('L'))
        return img

    @property
    @cached_result
    def width(self):
        src = getattr(self, '_saved_source', None)
        if src:
            return src.size[0]
        return self._eval_parameter('width', default=0)

    @property
    @cached_result
    def transparency(self):
        return min(1, max(0, self._eval_parameter('transparency', default=0)))

    @property
    @cached_result
    def keep_aspect(self):
        return bool(self._eval_parameter('keep_aspect', default=True))

    def draw_shape(self, size, **kwargs):
        # todo
        overlay = self._get_canvas(size)
        overlay.paste(self.source, (self.x, self.y), self.source)
        return overlay
