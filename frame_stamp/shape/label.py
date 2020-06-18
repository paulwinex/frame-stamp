from __future__ import absolute_import
from .base_shape import BaseShape
from PIL import ImageFont, ImageDraw, ImageFilter, Image
import string, os, html, re
import textwrap
from frame_stamp.utils import cached_result
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
        fit_to_parent      : Вписать текст в размер родительского объекта
        line_splitter      : символ по которому разделять строки для авто переноса.
                                None - по любому символу
                                " " - по словам
                                "/" - по частям пути
        move_splitter_to_next_line: Работает только при включенном fit_to_parent и line_splitter
                             true - символ разделения строки переносить на следующую строку
                             false - символ разделения строки оставлять на текущей строке
    """
    shape_name = 'label'
    special_characters = {
        '&;': ''
    }
    default_fonts_dir = os.path.dirname(os.path.dirname(__file__))
    _default_font_name = 'FreeSansBold.ttf' if not os.name == 'nt' else 'arial.ttf'

    @property
    @cached_result
    def text(self):
        """
        РЕсолвинг текста
        """
        text = self._data['text']
        if '$' in text:
            text = string.Template(text).substitute(**self.variables)
        text = self._render_special_characters(text)
        for match in re.finditer(r'`(.*?)`', text):
            res = str(self._eval_expression('text', match.group(1)))
            text = text.replace(match.group(0), res)
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
        if self.fit_to_parent:
            text = self._fir_to_parent_width(text, self.line_splitter)
        return text.strip()

    def _trunc_path(self, text, count, from_start=1):
        parts = os.path.normpath(text).split(os.path.sep)
        if from_start:
            return os.path.sep.join(parts[:count + 1])
        else:
            return os.path.sep.join(parts[-count:])

    def _render_special_characters(self, text):
        for char, val in self.special_characters.items():
            text = re.sub(char, val, text)
        return html.unescape(text)

    # def _get_parent_width_in_characters(self):
    #     """
    #     Получение ширины parent'а в символах
    #
    #     Returns
    #     -------
    #     width_characters: int
    #     """
    #     parent_width_pixels = self.parent.width
    #     # используем проверочную строку, чтобы вычислить ширину одного символа в пикселях,
    #     # зная ее длину в символах
    #     test_str = 'A testing string. The longer it is, the more accurate the results it produces'
    #     # делим ширину этой строки на количество символов и получаем соотношение
    #     pixel_to_char_ratio = self.font.getsize(test_str)[0] / len(test_str)
    #     # сначала округляем значение, тем самым получая более точный int после
    #     width_characters = int(round(parent_width_pixels / pixel_to_char_ratio))
    #     return width_characters

    def _fir_to_parent_width(self, text, divider=None):
        """
        Добавление переноса, если текст не помещается в размер парента

        Parameters
        ----------
        text: str

        Returns
        -------
        text: str
        """
        # parent_width_pixels = self.parent.width
        if self.parent.width >= self.font.getsize(text)[0]:
            # перенос не требуется
            return text
        single_char_width = self.font.getsize('a')[0]
        max_chars_in_line = self.parent.width // single_char_width
        if divider:     # разделяем по указанным символам
            if not any([x in text for x in divider]):
                # символы разделителя не найдены в тексте
                return text
            lines = self._split_text_by_divider(text, divider, self.move_splitter_to_next_line)
            joined_lines = []
            # соединяем строки пока есть достаточно ширины
            t = ''
            while lines:
                next_peace = lines.pop(0)
                # если общая длина прошлой и следующей строки меньше максимальной, то склеиваем их
                if len(t) + len(next_peace.rstrip()) < max_chars_in_line:
                    t += next_peace
                else:
                    # переходим к следующей строке
                    joined_lines.append(t)
                    t = next_peace.lstrip()
                if not lines:
                    joined_lines.append(t)
            text = '\n'.join(joined_lines).strip()
        else:
            # разделяем просто по словам или символам
            wrapper = textwrap.TextWrapper(width=max_chars_in_line,
                                           replace_whitespace=False)  # ставим это, чтобы не убивались исходные '\n'
            text = wrapper.fill(text=text)
        return text
        # # # находим все строки
        # # lines = text.split('\n')
        # # # находим самую длинную строку, чтобы по ней вычислить значение максимальной ширины текста
        # # longest_line = max(lines, key=len)
        #
        # # если она превышает ширину parent'a, начинаем делать wordwrap
        #
        #     # если в тексте есть И сепаратор (слэш, соответствующей текущей ОС) И расширение файла,
        #     # считаем его путем к файлу, вызываем соответствующий метод
        #     if os.path.sep in text and os.path.splitext(text):
        #         return self._add_new_lines_for_path(text)
        #     # если строк несколько, вычисляем wordwrap, иначе просто возвращаем текст как есть
        #     if len(lines) > 1:
        #         # максимальную допустимую ширину находим, сначала посчитав,
        #         # сколько символов приходится на один пиксель самой длинной строки
        #         char_to_pixel_ratio = len(longest_line) / self.font.getsize(longest_line)[0]
        #         # и потом умножив это на количество пикселей parent'a
        #         width_characters = int(round(parent_width_pixels * char_to_pixel_ratio))
        #         # импортим и создаем Wrapper
        #         import textwrap
        #         wrapper = textwrap.TextWrapper(width=width_characters,
        #                                        replace_whitespace=False)  # ставим это, чтобы не убивались исходные '\n'
        #         text = wrapper.fill(text=text)
        #     return text
        # return text

    # def _add_new_lines_for_path(self, path):
    #     """
    #     Добавление переносов для пути до файла (со слэшами)
    #
    #     Parameters
    #     ----------
    #     path: str
    #
    #     Returns
    #     -------
    #     newlined_path: str
    #     """
    #     newlined_path = ''
    #     sep = os.path.sep
    #     slash_split = path.split(sep)
    #     remainder = slash_split
    #     parent_width_characters = self._get_parent_width_in_characters()
    #
    #     while not len([char for char in sep.join(remainder) if char == sep]) < 2:
    #         path_variants = [sep.join(remainder[:i + 1]) for i in range(len(remainder)) if sep.join(remainder[:i + 1])]
    #         path_variants = [path_variants[i] + sep if i < len(path_variants) - 1 else path_variants[i] for i in
    #                          range(len(path_variants))]
    #         longest_variant = [path for path in path_variants if len(path) < parent_width_characters][-1]
    #         newlined_path += longest_variant + '\n'
    #         remainder = sep.join(remainder).replace(longest_variant, '').split(sep)
    #
    #     remainder = sep.join(remainder)
    #     newlined_path = newlined_path + remainder
    #     return newlined_path

    def _split_text_by_divider(self, text, divider, move_divider_to_next_line=False):
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

    @property
    @cached_result
    def font_size(self) -> int:
        size = self._eval_parameter('font_size')  # type: int
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
                # logger.debug('Font {} not found, use default'.format(self.font_name))
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
        f = self._eval_parameter('font_name', default=None)
        if not os.path.exists(f):
            f = os.path.join(self.default_fonts_dir, 'fonts', f)
            if not f.endswith('ttf'):
                f += '.ttf'
        return f

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

    @property
    @cached_result
    def fit_to_parent(self):
        return bool(self._eval_parameter('fit_to_parent', default=False))

    @property
    @cached_result
    def line_splitter(self):
        return self._eval_parameter('line_splitter', default=None)

    @property
    @cached_result
    def move_splitter_to_next_line(self):
        return self._eval_parameter('move_splitter_to_next_line', default=None)

    @cached_result
    def get_size(self):
        """
        Размер текста в пикселях

        Returns
        -------
        (x,y): tuple
        """
        lines = self.text.split('\n')
        x = max([self.font.getsize(text)[0] for text in lines])
        y = 0
        base_line = self.font.font.height - self.font.font.descent
        line_height = base_line
        # находим размер самого маленького символа и основываем размер строки на нем.
        # это сделано чтобы из-за символов, границы которых больше (вроде "_" или "y"),
        # весь текст не приподнимался
        # smallest_char_size = min([self.draw.textsize(char, font=self.font)[1] for char in [line[0] for line in lines]])
        # line_height = smallest_char_size
        for line in lines:
            # если строк несколько, добавляем по spacing кол-ву пикселей на каждую из них
            # но не добавляем последней строке, чтобы она не приподнималась над нижней линией
            if len(lines) > 1:
                y += line_height + self.spacing
            # если строка одна или это последняя строка, просто прибавляем размер меньшего символа
            else:
                y += line_height
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
        # self.draw = drw
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
            drw.rectangle((self.x - ofs, self.y - ofs, self.right + ofs, self.bottom + ofs), fill=clr)
            canvas = Image.alpha_composite(bd, canvas)
        return canvas
