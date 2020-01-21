from __future__ import absolute_import
from .base_shape import BaseShape
from PIL import ImageFont
import string


class LabelShape(BaseShape):
    """
    Текст

    Allowed parameters:
        x
        y
        text
        text_color
        font_size
        font
        margin
        bound:  (100, 0)
        parent
    """
    shape_name = 'label'

    @property
    def text(self):
        text = self._eval_parameter('text')
        if '$' in text:
            text = string.Template(text).substitute(**self.context)
        return text

    @property
    def font_size(self) -> int:
        size = self._eval_parameter('font_size')    # type: int
        if size == 0:
            raise ValueError('Font size can`t be zero. Shape "{}"'.format(self))
        return size

    @property
    def font(self):
        fnt = ImageFont.truetype(self.font_name, int(self.font_size))
        return fnt

    @property
    def font_name(self):
        return self._eval_parameter('font_name')

    @property
    def bound(self) -> list:
        """
        Ограничение размера текста

        Returns
        -------
        tuple
        """
        try:
            bound = self._eval_parameter('bound')
        except KeyError:
            return []
        if not bound:
            return []
        return [self._eval_parameter(x) for x in bound]

    @property
    def text_color(self):
        return self._eval_parameter('text_color')

    def render(self, img, **kwargs):
        bound = self.bound
        if bound:
            # todo: не реализовано!
            import textwrap
            margin = offset = 40
            for line in textwrap.wrap(self.text, width=40):
                img.text((margin, offset), line, font=self.font, fill=self.text_color)
                offset += self.font.getsize(line)[1]
        else:
            img.text((self.x, self.y), self.text, font=self.font, fill=self.text_color)


