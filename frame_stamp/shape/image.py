from __future__ import absolute_import
from PIL import Image
from .base_shape import BaseShape
from pathlib import Path
import string


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
        if '$' in value:
            value = string.Template(value).substitute(**self.context)
        path = Path(value).expanduser().resolve()
        if not path.exists():
            raise IOError(f'Path not exists: {path.as_posix()}')
        return Image.open(path.as_posix())

    @property
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
            # применение прозрачности
            # transp = self.transparency
            # if transp:
            #      img.putalpha(min(max(int(255*transp), 0), 255))
            # ресайз
            if self.keep_aspect:
                img.thumbnail(self.size, Image.ANTIALIAS)
            else:
                img = img.resize(self.size, Image.ANTIALIAS)

            self.__dict__['_saved_source'] = img.convert('RGBA')
        return self.__dict__['_saved_source']

    # @property
    # def mask(self):
    #     if '_saved_mask' not in self.__dict__:
    #         mask = self._data.get('mask')
    #         if not mask:
    #             return
    #         img = self._get_image(mask)
    #         if self.keep_aspect:
    #             img.thumbnail(self.size, Image.ANTIALIAS)
    #         else:
    #             img = img.resize(self.size, Image.ANTIALIAS)
    #         self.__dict__['_saved_mask'] = img.convert('L')
    #     return self.__dict__['_saved_mask']

    @property
    def width(self):
        # todo: высота более приоритетна, поэтому надо рассчитать правильную ширину если keep_aspect=True
        return self._eval_parameter('width')

    @property
    def transparency(self):
        return self._eval_parameter('transparency', default=0)

    @property
    def keep_aspect(self):
        return bool(self._eval_parameter('keep_aspect'))

    def render(self, img, **kwargs):
        # todo
        self.source_image.paste(self.source, (self.x, self.y), self.source)
