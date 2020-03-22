from __future__ import absolute_import
from .base_shape import BaseShape
from PIL import ImageFont, ImageDraw
import string, os, html, re
from ..utils import cached_result


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
    special_characters = {
        '&;': ''
    }

    @property
    @cached_result
    def text(self):
        text = self._data['text']
        if '$' in text:
            text = string.Template(text).substitute(**self.variables)
        text = self._render_special_characters(text)
        text = str(self._eval_expression('text', text) or text)
        if self.truncate_path:
            text = self._trunc_path(text, self.truncate_path, 1)
        elif self.ltruncate_path:
            text = self._trunc_path(text, self.ltruncate_path, 0)
        if self.lower:
            text = text.lower()
        if self.truncate and len(text) > self.truncate:
            text = text[:self.truncate] + '...'
        if self.ltruncate and len(text) > self.ltruncate:
            text = '...' + text[-self.ltruncate:]
        if self.upper:
            text = text.upper()
        if self.title:
            text = text.title()
        if self.zfill:
            text = text.zfill(self.zfill)
        return text

    def _trunc_path(self, text, count, from_start=1):
        parts = os.path.normpath(text).split(os.path.sep)
        if from_start:
            return os.path.sep.join(parts[:count+1])
        else:
            return os.path.sep.join(parts[-count:])

    def _render_special_characters(self, text):
        for char, val in self.special_characters.items():
            text = re.sub(char, val, text)
        return html.unescape(text)

    @property
    @cached_result
    def font_size(self) -> int:
        size = self._eval_parameter('font_size')    # type: int
        if size == 0:
            raise ValueError('Font size can`t be zero. Shape "{}"'.format(self))
        return size

    @property
    @cached_result
    def spacing(self):
        return self._eval_parameter('text_spacing')

    @property
    @cached_result
    def truncate(self):
        return self._eval_parameter('truncate', default=None)

    @property
    @cached_result
    def ltruncate(self):
        return self._eval_parameter('ltruncate', default=None)

    @property
    @cached_result
    def truncate_path(self):
        return self._eval_parameter('truncate_path', default=None)

    @property
    @cached_result
    def ltruncate_path(self):
        return self._eval_parameter('ltruncate_path', default=None)

    @property
    @cached_result
    def title(self):
        return self._eval_parameter('title', default=False)

    @property
    @cached_result
    def upper(self):
        return self._eval_parameter('upper', default=False)

    @property
    @cached_result
    def lower(self):
        return self._eval_parameter('lower', default=False)

    @property
    @cached_result
    def zfill(self):
        return self._eval_parameter('zfill', default=False)

    @property
    @cached_result
    def font(self):
        try:
            fnt = ImageFont.truetype(self.font_name, int(self.font_size))
        except OSError:
            fnt = ImageFont.truetype(self.default_font, int(self.font_size))
        return fnt

    @property
    @cached_result
    def font_name(self):
        return self._eval_parameter('font_name', default=None) or self.default_font or 'OpenSansBold.ttf'

    @property
    @cached_result
    def default_font(self):
        df = self._eval_parameter('default_font', default=None)
        if not df:
            df = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fonts', self._eval_parameter('default_font_name'))
        return df

    @property
    @cached_result
    def color(self):
        clr = self._eval_parameter('text_color')
        if isinstance(clr, list):
            clr = tuple(clr)
        return clr

    @cached_result
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
