from __future__ import absolute_import
from .base_shape import BaseShape
from PIL import ImageFont, ImageDraw
import string, os


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
        text = str(self._eval_expression('text', text) or text)
        tr = self.truncate
        if tr and len(text) > tr:
            text = text[:tr] + '...'
        ltr = self.ltruncate
        if ltr:
            text = '...' + text[-ltr:]
        if self.lower:
            text = text.lower()
        if self.upper:
            text = text.upper()
        if self.title:
            text = text.title()
        if self.zfill:
            text = text.zfill(self.zfill)
        return text

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
    def truncate(self):
        return self._eval_parameter('truncate', default=None)

    @property
    def ltruncate(self):
        return self._eval_parameter('ltruncate', default=None)

    @property
    def title(self):
        return self._eval_parameter('title', default=False)

    @property
    def upper(self):
        return self._eval_parameter('upper', default=False)

    @property
    def lower(self):
        return self._eval_parameter('lower', default=False)

    @property
    def zfill(self):
        return self._eval_parameter('zfill', default=False)

    @property
    def font(self):
        try:
            fnt = ImageFont.truetype(self.font_name, int(self.font_size))
        except OSError:
            fnt = ImageFont.truetype(self.default_font, int(self.font_size))
        return fnt

    @property
    def font_name(self):
        return self._eval_parameter('font_name', default=None) or self.default_font or 'OpenSansBold.ttf'

    @property
    def default_font(self):
        df = self._eval_parameter('default_font', default=None)
        if not df:
            df = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fonts', self._eval_parameter('default_font_name'))
        return df

    @property
    def color(self):
        clr = self._eval_parameter('text_color')
        if isinstance(clr, list):
            clr = tuple(clr)
        return clr

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

    def draw_shape(self, size, **kwargs):
        canvas = self._get_canvas(size)
        img = ImageDraw.Draw(canvas)
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
        return canvas
