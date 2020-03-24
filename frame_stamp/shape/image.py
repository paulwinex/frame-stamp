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
    def source(self):
        source = self._data.get('source')
        if not source:
            raise RuntimeError('Image source not set')
        img = self._get_image(source)
        # применение прозрачности и маски
        img = self.apply_mask(img, self.mask, self.transparency)
        return img

    @property
    @cached_result
    def source_resized(self):
        """
        Исходник картинки для рисования

        Returns
        -------
        Image.Image
        """
        img = self.source
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
        return img

    @property
    @cached_result
    def height(self):
        h = super(ImageShape, self).height
        if h:
            return h
        w = super(ImageShape, self).width
        if not w:
            return self.source.size[1]
        else:
            if self.keep_aspect:
                return int(w * (self.source.size[0]/self.source.size[1]))
            else:
                return self.source.size[1]

    @property
    @cached_result
    def width(self):
        w = super(ImageShape, self).width
        if w:
            return w
        h = super(ImageShape, self).height
        if not h:
            return self.source.size[0]
        else:
            if self.keep_aspect:
                return int(h * (self.source.size[0]/self.source.size[1]))
            else:
                return self.source.size[0]

    @property
    @cached_result
    def size(self):
        return self.width, self.height

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
    def transparency(self):
        return min(1, max(0, self._eval_parameter('transparency', default=0)))

    @property
    @cached_result
    def keep_aspect(self):
        return bool(self._eval_parameter('keep_aspect', default=True))

    def draw_shape(self, size, **kwargs):
        overlay = self._get_canvas(size)
        overlay.paste(self.source_resized, (self.x, self.y), self.source_resized)
        return overlay
