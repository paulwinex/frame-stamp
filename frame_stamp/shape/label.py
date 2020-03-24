from __future__ import absolute_import
from .base_shape import BaseShape
from PIL import ImageFont, ImageDraw, ImageFilter, Image
import string, os, html, re
from ..utils import cached_result
import cgflogging

logger = cgflogging.getLogger(__name__)


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
    default_fonts_dir = os.path.dirname(os.path.dirname(__file__))
    _default_font_name = 'FreeSansBold.ttf'

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
        text = self._add_new_lines(text)
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

    def _add_new_lines(self, text):
        """
        Добавление переноса если текст не помещается в размер парента
        """
        # TODO
        return text

    @property
    @cached_result
    def font_size(self) -> int:
        size = self._eval_parameter('font_size')    # type: int
        if size == 0:
            raise ValueError('Font size can`t be zero. Shape "{}"'.format(self))
        return int(size)

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
        """
        Возвращает готовый шрифт для рендера
        """
        if self.font_name:
            try:
                fnt = ImageFont.truetype(self.font_name or self.default_font_name, int(self.font_size))
            except (OSError, AttributeError):
                logger.debug('Font {} not found, use default'.format(self.font_name))
                fnt = ImageFont.truetype(self.default_font_name, self.font_size)
        else:
            fnt = ImageFont.truetype(self.default_font_name, self.font_size)
        return fnt

    @property
    @cached_result
    def font_name(self):
        """
        Путь к шрифту или имя шрифта из стандартных директорий
        """
        return self._eval_parameter('font_name', default=None)

    @property
    @cached_result
    def default_font_name(self):
        """
        Путь или имя шрифта по умолчанию
        """
        default_name = self._eval_parameter('default_font_name', default=None) or self._default_font_name
        df = self._eval_parameter('default_font', default=None)
        if not df:
            df = os.path.join(self.default_fonts_dir, 'fonts', default_name)
        return df

    @property
    @cached_result
    def color(self):
        clr = self._eval_parameter('text_color')
        if isinstance(clr, list):
            clr = tuple(clr)
        return clr

    @property
    @cached_result
    def outline(self):
        return self._eval_parameter('outline', default={})

    @property
    @cached_result
    def backdrop(self):
        return self._eval_parameter('backdrop', default=None)

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
        drw = ImageDraw.Draw(canvas)
        is_multiline = '\n' in self.text
        printer = drw.multiline_text if is_multiline else drw.text
        text_args = dict(
            font=self.font,
            fill=self.color
        )
        if is_multiline:
            text_args['spacing'] = self.spacing
            if self.align_h:
                text_args['align'] = self.align_h
        if self.outline:
            # получаем словарь с параметрами обводки
            outline_text_args = text_args.copy()
            if isinstance(self.outline, (int, float)):
                outline = {'width': self.outline}
            elif isinstance(self.outline, dict):
                outline = self.outline.copy()
            else:
                raise TypeError('Outline parameter must be type of dict or number')
            # заменяем цвет в аргументах
            outline_text_args['fill'] = outline.get('color', 'black')
            # рисуем черный текст
            printer((self.x_draw, self.y_draw), self.text, **outline_text_args)
            # размвка
            canvas = canvas.filter(ImageFilter.GaussianBlur(outline.get('width', 3)))
            # фильтр жёсткости границ
            x = 0
            y = outline.get('hardness', 10)
            STROKE = type('STROKE', (ImageFilter.BuiltinFilter,),
                          {'filterargs': ((3, 3), 1, 0, (x, x, x, x, y, x, x, x, x,))})
            canvas = canvas.filter(STROKE)
            drw = ImageDraw.Draw(canvas)
            # пересоздаём паинтер
            printer = drw.multiline_text if is_multiline else drw.text
        printer((self.x_draw, self.y_draw), self.text, **text_args)
        if self.backdrop:
            if isinstance(self.backdrop, str):
                backdrop = {'color': self.backdrop, "offset": 5}
            elif isinstance(self.backdrop, dict):
                backdrop = self.backdrop.copy()
            else:
                raise TypeError('Outline parameter must be type of dict or number')
            bd = self._get_canvas(size)
            drw = ImageDraw.Draw(bd)
            ofs = backdrop.get('offset', 5)
            clr = backdrop.get('color', 'black')
            if isinstance(clr, list):
                clr = tuple(clr)
            drw.rectangle((self.x-ofs, self.y-ofs, self.right+ofs, self.bottom+ofs), fill=clr)
            canvas = Image.alpha_composite(bd, canvas)
        return canvas
