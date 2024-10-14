from __future__ import absolute_import

from pathlib import Path

from .base_shape import BaseShape
from PIL import ImageFont, ImageDraw, ImageFilter, Image
import string, os, html, re
import textwrap
from frame_stamp.utils import cached_result
import logging

logger = logging.getLogger(__name__)


class LabelShape(BaseShape):
    """
    Text

    Allowed parameters:
        text               : Source text. Supported formatting from context. Example: "Project: $project_name"
        text_spacing       : Spacing between lines in multiline text. Default 0
        text_color         : Color of text
        font_size          : Font size
        font_name          : Font name or path
        fit_to_parent      : Fit text to parent size
        line_splitter      : Character to separate multiline text.
                                None - any character
                                " " - by words
                                "/" - by path parts
        move_splitter_to_next_line: Works only with fit_to_parent и line_splitter
                             true - separated character moved to next line
                             false - separated character live on current line
        max_lines_count
        lmax_lines_count
        truncate
        ltruncate
        truncate_path
        ltruncate_path
        truncate_to_parent
        ltruncate_to_parent
        title
        upper
        lower
        zfill
        outline
        backdrop

    NOTE
        This class implements a custom calculation of font height. By default, the height will be the maximum height
        in pixels. However, this class calculates the height based on the metric lines of the font itself. Thus,
        elements below the font baseline and above the capital line do not fall within the height. Because of this,
        there are offsets in various places in the calculations.

    """
    shape_name = 'label'
    special_characters = {
        '&;': ''
    }
    default_fonts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fonts')
    _default_font_name = 'OpenSansBold.ttf' if not os.name == 'nt' else 'arial.ttf'

    @property
    @cached_result
    def text(self) -> str:
        """
        Resolve text value
        """
        text = self._data['text']
        l_pad = r_pad = ''
        left_pad_match = re.match(r"^\s+", text)
        if left_pad_match:
            l_pad = left_pad_match.group(0)
        right_pad_match = re.match(r"\s+$", text)
        if right_pad_match:
            r_pad = right_pad_match.group(0)
        text = text.strip()
        if '$' in text:
            ctx = {**self.defaults, **self.variables}
            text = self._render_variables(text, ctx)
        text = self._render_special_characters(text)
        for match in re.finditer(r'`(.*?)`', text):
            res = str(self._eval_expression('text', match.group(0)))
            text = text.replace(match.group(0), res)
        if self.zfill:
            text = text.zfill(self.zfill)
        if self.prefix:
            text = self. prefix + text
        if self.suffix:
            text = text + self.suffix
        if self.format_date:
            text = self._format_date_from_context(text)
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

        if self.fit_to_parent:
            text = self._fit_to_parent_width(text, self.line_splitter)
        elif self.truncate_to_parent or self.ltruncate_to_parent:
            text = self._truncate_to_parent(text, left=self.ltruncate_to_parent)
        return l_pad+text.strip()+r_pad

    def _trunc_path(self, text, count, from_start=1):
        """
        Clip path by max element count
        """
        parts = os.path.normpath(text).split(os.path.sep)
        if from_start:
            return os.path.sep.join(parts[:count + 1])
        else:
            return os.path.sep.join(parts[-count:])

    def _truncate_to_parent(self, text, left=False):
        if self.parent.width >= self.font.getsize(text)[0]:
            # перенос не требуется
            return text
        single_char_width = self.font.getsize('a')[0]
        max_chars_in_line = self.parent.width // single_char_width
        if len(text) > max_chars_in_line:
            if left:
                text = '...'+text[-max_chars_in_line+3:]
            else:
                text = text[:max_chars_in_line-3] + '...'
        return text

    def _render_special_characters(self, text) -> str:
        """
        Render of special HTML elements
        """
        for char, val in self.special_characters.items():
            text = re.sub(char, val, text)
        return html.unescape(text)

    def _fit_to_parent_width(self, text, divider=None) -> str:
        """
        Adding line breaks if the text does not fit the parent size.

        Parameters
        ----------
        text: str

        Returns
        -------
        text: str
        """
        single_char_width = self.font.getlength('a') if hasattr(self.font, 'getlength') else self.font.getsize('a')[0]
        if self.parent.width <= single_char_width:
            # перенос не требуется
            return text

        max_chars_in_line = int(max([1, self.parent.width // single_char_width]))
        if divider:     # разделяем по указанным символам
            if not any([x in text for x in divider]):
                # символы разделителя не найдены в тексте
                return text
            lines = self._split_text_by_divider(text, divider, self.move_splitter_to_next_line)
            joined_lines = []
            # join lines
            t = ''
            while lines:
                next_peace = lines.pop(0)
                # if full length previous line and next line less than maximum - join them
                if len(t) + len(next_peace.rstrip()) < max_chars_in_line:
                    t += next_peace
                else:
                    # to nex tline
                    joined_lines.append(t)
                    t = next_peace.lstrip()
                if not lines:
                    joined_lines.append(t)
        else:
            # separate by word or character
            wrapper = textwrap.TextWrapper(width=max_chars_in_line,
                                           replace_whitespace=False)  # to save existing '\n'
            _text = wrapper.fill(text=text)
            joined_lines = _text.split('\n')

        # limit maximum lines count
        if self.max_lines_count and len(joined_lines) > self.max_lines_count:
            joined_lines = joined_lines[:self.max_lines_count]
            joined_lines[-1] = joined_lines[-1] + '...'
        elif self.lmax_lines_count and len(joined_lines) > self.lmax_lines_count:
            joined_lines = joined_lines[-self.lmax_lines_count:]
            joined_lines[0] = '...' + joined_lines[0]

        text = '\n'.join(joined_lines).strip()

        return text

    def _split_text_by_divider(self, text, divider, move_divider_to_next_line=False) -> list:
        """
        Divide text by character
        """
        parts = []
        line = ''
        for char in text:
            if char in divider:
                if move_divider_to_next_line:
                    parts.append(line)
                    line = char
                else:
                    line += char
                    parts.append(line)
                    line = ''
            else:
                line += char
        if line:
            parts.append(line)
        return parts

    def _format_date_from_context(self, text):
        """
        Text example:
        text = "Date: {:%Y.%m.%d %H:%I}"

        Returns
        -------
        str
        """
        from datetime import datetime
        ctx = {**self.defaults, **self.variables}
        date = datetime.fromtimestamp(ctx.get('timestamp')) or datetime.now()
        for dt_str in re.findall(r'{:.+?}', text):
            if not re.findall(r'%\w', dt_str):
                continue
            try:
                formatted = dt_str.format(date)
            except KeyError:
                continue
            text = text.replace(dt_str, formatted)
        return text

    @property
    @cached_result
    def font_size(self) -> int:
        """Font size"""
        size = self._eval_parameter('font_size')  # type: int
        if size == 0:
            raise ValueError('Font size can`t be zero. Shape "{}"'.format(self))
        return max(1, int(size))

    @property
    @cached_result
    def spacing(self):
        """Distance between lines"""
        return self._eval_parameter('text_spacing', default=0)

    @property
    @cached_result
    def truncate(self) -> int:
        """Clip line by character count"""
        return self._eval_parameter('truncate', default=None)

    @property
    @cached_result
    def ltruncate(self) -> int:
        """Clip line by character count from left"""
        return self._eval_parameter('ltruncate', default=None)

    @property
    @cached_result
    def truncate_path(self) -> int:
        """Обрезка пути с ограничением количества элементов пути"""
        return self._eval_parameter('truncate_path', default=None)

    @property
    @cached_result
    def ltruncate_path(self) -> int:
        """Обрезка пути слева"""
        return self._eval_parameter('ltruncate_path', default=None)

    @property
    @cached_result
    def truncate_to_parent(self) -> int:
        """Обрезка строки чтобы она вписалась в ширину парента"""
        return self._eval_parameter('truncate_to_parent', default=None)

    @property
    @cached_result
    def ltruncate_to_parent(self) -> int:
        """Обрезка строки слева чтобы она вписалась в ширину парента"""
        return self._eval_parameter('ltruncate_to_parent', default=None)

    @property
    @cached_result
    def title(self) -> str:
        """Apply function title()"""
        return self._eval_parameter('title', default=False)

    @property
    @cached_result
    def upper(self) -> str:
        """Apply function upper()"""
        return self._eval_parameter('upper', default=False)

    @property
    @cached_result
    def lower(self) -> str:
        """Apply function lower()"""
        return self._eval_parameter('lower', default=False)

    @property
    @cached_result
    def zfill(self) -> str:
        """Apply function zfill"""
        return self._eval_parameter('zfill', default=False)

    @property
    @cached_result
    def font(self) -> ImageFont:
        """
        Возвращает готовый шрифт для рендера
        """
        font = self._resolve_font_name(self.font_name)
        return ImageFont.FreeTypeFont(font, self.font_size)

    @property
    @cached_result
    def font_name(self) -> str:
        """
        Path to font or font name
        """
        return self._eval_parameter('font_name', default=None) or self._default_font_name

    # @property
    # @cached_result
    # def default_font_name(self):
    #     """
    #     Путь или имя шрифта по умолчанию
    #     """
    #     default_name = self._eval_parameter('default_font_name', default=None) or self._default_font_name
    #     df = self._eval_parameter('default_font', default=None)
    #     if not df:
    #         df = default_name
    #     return df

    @property
    @cached_result
    def color(self):
        """
        Font color
        """
        clr = self._eval_parameter('text_color')
        if isinstance(clr, list):
            clr = tuple(clr)
        return clr

    @property
    @cached_result
    def outline(self):
        """
        Add outline
        """
        return self._eval_parameter('outline', default={})

    @property
    @cached_result
    def backdrop(self):
        """
        Add backdrop
        """
        return self._eval_parameter('backdrop', default=None)

    @property
    @cached_result
    def fit_to_parent(self):
        """
        Fit string to parent's width with line wrap
        """
        return bool(self._eval_parameter('fit_to_parent', default=False))

    @property
    @cached_result
    def line_splitter(self):
        """
        Character to split a line when wrapping to a new line
        """
        return self._eval_parameter('line_splitter', default=None)

    @property
    @cached_result
    def move_splitter_to_next_line(self):
        """
        Determines where the delimiter character will stay. On the current line or on a new
        """
        return self._eval_parameter('move_splitter_to_next_line', default=None)

    @property
    @cached_result
    def max_lines_count(self):
        """
        Limit on the number of transitions to a new line. After that the line is cut off
        """
        return self._eval_parameter('max_lines_count', default=None)

    @property
    @cached_result
    def lmax_lines_count(self):
        """
        Limit on the number of transitions to a new line. The string is truncated from the beginning
        """
        return self._eval_parameter('lmax_lines_count', default=None)

    @property
    @cached_result
    def format_date(self):
        return self._eval_parameter('format_date', default=False)

    @property
    @cached_result
    def suffix(self):
        return self._eval_parameter('suffix', default=None)

    @property
    @cached_result
    def prefix(self):
        """
        Example:
             "text": "$version", zfill=3, prefix="v" -> "v001"
        """
        return self._eval_parameter('prefix', default=False)

    @cached_result
    def get_size(self) -> (int, int):
        """
        Font size in pixels
        """
        # общая высота текста без учета элементов под бейзлойном
        text_height = ((self.get_font_metrics()['font_height']+self.spacing)
                       * len(self.text.split('\n'))) - self.spacing
        # общая ширина текста по самой длинной строке
        text_width = max([self.font.getbbox(text)[2] for text in self.text.split('\n')])
        return text_width, text_height

    @property
    def width(self):
        return self.get_size()[0]

    @property
    def height(self):
        return self.get_size()[1]

    @property
    def y_draw(self):
        return super(LabelShape, self).y_draw - self.get_font_metrics()['offset_y']     # фикс по высоте, убираем верхнюю часть шрфита до высоты капса

    def _resolve_font_name(self, font_name) -> str:
        """
        Looking for font by name
        """
        from ..utils import b64
        # is base64
        if b64.is_b64(font_name):
            return b64.b64_str_to_file(font_name)
        # has ext?
        if not font_name.endswith('ttf') and not Path(font_name).suffix:
            font_name += '.ttf'
        # is abs?
        if os.path.exists(font_name):
            return font_name
        # in custom resource dirs
        try:
            return self.get_resource_file(font_name)
        except OSError:
            pass
        # default fonts
        font_file = os.path.join(self.default_fonts_dir, font_name)
        if os.path.exists(font_file):
            return font_file
        # from system fonts
        try:
            ImageFont.truetype(font_name, 10)
            return font_name
        except OSError:
            pass
        raise LookupError('Font "{}" not found'.format(font_name))

    def get_font_metrics(self):
        (_, font_height), (_, offset_y) = self.font.font.getsize('A')
        return dict(
            font_height=font_height,
            offset_y=offset_y
        )

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
            text_args['spacing'] = self.spacing - self.get_font_metrics()['offset_y']
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
            if isinstance(outline_text_args['fill'], list):
                outline_text_args['fill'] = tuple(outline_text_args['fill'])
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
            drw.rectangle((self.x - ofs, self.y - ofs, self.right + ofs, self.bottom + ofs), fill=clr)
            canvas = Image.alpha_composite(bd, canvas)
        return canvas
