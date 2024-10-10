from __future__ import absolute_import
import re
from PIL import Image, ImageChops, ImageOps
from .base_shape import BaseShape
from frame_stamp.utils import cached_result
import logging

logger = logging.getLogger(__name__)


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
        from ..utils import b64
        if value == '$source':  # source image of the frame, not to be confused with the source of the shape itself
            # return source frame image
            return self.source_image.copy()
        elif b64.is_b64(value):
            return b64.b64_str_to_image(value)
        # looking for file
        res = self.get_resource_file(value)
        if res:
            return Image.open(str(res))
        raise IOError(f'Path not exists: ({value}) {res}')

    @property
    def source(self):
        # source = self._data.get('source')
        source = self._eval_parameter('source')
        if not source:
            raise RuntimeError('Image source not set')
        img = self._get_image(source)
        # apply mask and transparency
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
        # resize
        if self.size != img.size:
            target_size = list(self.size)
            if target_size[0] == 0:
                target_size[0] = img.size[0]
            if target_size[1] == 0:
                target_size[1] = img.size[1]
            img = ImageOps.fit(img, target_size, Image.Resampling.LANCZOS)
        return img

    def _resize_values(self, src_size, trg_size):
        a1 = trg_size[0] / src_size[0]
        a2 = trg_size[1] / src_size[1]
        scale = min([a1, a2])
        result = [int(x * scale) for x in src_size]
        return result

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
                return int(w * (self.source.size[1]/self.source.size[0]))
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
    def source_size(self):
        return self.source.size

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

    @property
    @cached_result
    def multiply_color(self):
        clr = self._eval_parameter('multiply_color', default=None)
        if clr is not None:
            if isinstance(clr, (list, tuple)):
                return tuple(clr)
            elif isinstance(clr, str):
                m = re.match(r"rgb\(([\d\s,]+)\)$", clr)
                if m:
                    return tuple(map(int, m.group(1).split(',')))
                m = re.match(r"hsv\(([\d\s,]+)\)$", clr)
                if m:
                    import colorsys
                    hsv = tuple(map(int, m.group(1).split(',')))
                    return tuple(map(lambda x: int(x*255), colorsys.hsv_to_rgb(*map(lambda x: x/255, hsv))))
                raise ValueError(f'Unknown color format {clr}')
            else:
                raise TypeError(f'Invalid color type {clr}: {type(clr)}')

    def _apply_multiply_color(self, img: Image):
        if self.multiply_color:
            return ImageChops.multiply(img, Image.new(
                'RGBA',
                img.size,
                color=self.multiply_color).convert('RGBA'))
        return img

    def draw_shape(self, size, **kwargs):
        overlay = self._get_canvas(size)
        img = self._apply_multiply_color(self.source_resized)
        overlay.paste(img, (self.x, self.y), img)
        return overlay
