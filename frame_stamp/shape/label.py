from __future__ import absolute_import
from .base_shape import BaseShape
from PIL import ImageFont
import string


class LabelShape(BaseShape):
    """
    Текст

    Allowed parameters:
        text               : Текст. Поддерживается форматирование переменных их конеткста "Project: $project_name"
        text_spacing       : Расстояние между строк в многосточном тексте. По умолчанию 0
        font_size          : Размер шрифта
        font_name          : Используемый шрифт
    """
    shape_name = 'label'

    @property
    def text(self):
        text = self._data['text']
        if '$' in text:
            text = string.Template(text).substitute(**self.variables)
        # if text.startswith('='):
        text = self._eval_expression('text', text) or text
        return str(text)

    @property
    def font_size(self) -> int:
        size = self._eval_parameter('font_size')    # type: int
        if size == 0:
            raise ValueError('Font size can`t be zero. Shape "{}"'.format(self))
        return size

    @property
    def spacing(self):
        return self._eval_parameter('text_spacing')

    @property
    def font(self):
        fnt = ImageFont.truetype(self.font_name, int(self.font_size))
        return fnt

    @property
    def font_name(self):
        return self._eval_parameter('font_name')

    @property
    def color(self):
        return self._eval_parameter('text_color')

    def get_size(self):
        """
        Размер текста в пикселях

        Returns
        -------
        tuple
        """
        x = max([self.font.getsize(text)[0] for text in self.text.split('\n')])
        y = sum([self.font.getsize(text)[1] for text in self.text.split('\n')]) + \
            (self.spacing * (len(self.text.split('\n'))-1))
        return x, y

    @property
    def width(self):
        return self.get_size()[0]

    @property
    def height(self):
        return self.get_size()[1]

    def render(self, img, **kwargs):
        is_multiline = '\n' in self.text
        printer = img.multiline_text if is_multiline else img.text
        text_args = dict(
            font=self.font,
            fill=self.color
        )
        if is_multiline:
            text_args['spacing'] = self.spacing
            if self.align_h:
                text_args['align'] = self.align_h
        printer((self.x_draw, self.y_draw), self.text, **text_args)
        return img




