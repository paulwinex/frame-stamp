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
        text_color
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
        Класс реализует нестандартный рассчет высоты шрфита. По умолчанию высотой будет максимальная высота в пикселях.
        Но данный класс рассчитывае высоту по метрическим линиям самого шрифта. Таким образом элементы под базовой линией
        шрифта и над линией капса в высоту не попадают. Изза этого есть офсеты в различных местах рассчётов.

    """
    shape_name = 'label'
    special_characters = {
        '&;': ''
    }
    default_fonts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fonts')
    _default_font_name = 'FreeSansBold.ttf' if not os.name == 'nt' else 'arial.ttf'

    @property
    @cached_result
    def text(self):
        """
        Ресолвинг текста
        """
        text = self._data['text']
        if '$' in text:
            ctx = {**self.defaults, **self.variables}
            text = string.Template(text).substitute(ctx)
        text = self._render_special_characters(text)
        for match in re.finditer(r'`(.*?)`', text):
            res = str(self._eval_expression('text', match.group(1)))
            text = text.replace(match.group(0), res)
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
        if self.zfill:
            text = text.zfill(self.zfill)
        if self.fit_to_parent:
            text = self._fit_to_parent_width(text, self.line_splitter)
        elif self.truncate_to_parent or self.ltruncate_to_parent:
            text = self._truncate_to_parent(text, left=self.ltruncate_to_parent)
        return text.strip()

    def _trunc_path(self, text, count, from_start=1):
        """
        Обрезка пути по максимальному количеству элементов
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

    def _render_special_characters(self, text):
        """
        Рендеринг специальных символов HTML
        """
        for char, val in self.special_characters.items():
            text = re.sub(char, val, text)
        return html.unescape(text)

    def _fit_to_parent_width(self, text, divider=None):
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
        max_chars_in_line = max([1, self.parent.width // single_char_width])
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
        else:
            # разделяем просто по словам или символам
            wrapper = textwrap.TextWrapper(width=max_chars_in_line,
                                           replace_whitespace=False)  # ставим это, чтобы не убивались исходные '\n'
            _text = wrapper.fill(text=text)
            joined_lines = _text.split('\n')

        # обрезка максимального количества строк
        if self.max_lines_count and len(joined_lines) > self.max_lines_count:
            joined_lines = joined_lines[:self.max_lines_count]
            joined_lines[-1] = joined_lines[-1] + '...'
        elif self.lmax_lines_count and len(joined_lines) > self.lmax_lines_count:
            joined_lines = joined_lines[-self.lmax_lines_count:]
            joined_lines[0] = '...' + joined_lines[0]

        text = '\n'.join(joined_lines).strip()

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

    def _split_text_by_divider(self, text, divider, move_divider_to_next_line=False):
        """
        Разделение текста по указанному символу

        Returns
        -------
        list
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
        """Размер шрифта"""
        size = self._eval_parameter('font_size')  # type: int
        if size == 0:
            raise ValueError('Font size can`t be zero. Shape "{}"'.format(self))
        return int(size)

    @property
    @cached_result
    def spacing(self):
        """Расстояние между строками"""
        return self._eval_parameter('text_spacing')

    @property
    @cached_result
    def truncate(self):
        """Обрезка строки по количеству символов"""
        return self._eval_parameter('truncate', default=None)

    @property
    @cached_result
    def ltruncate(self):
        """Обрезка строки по количеству символов слева"""
        return self._eval_parameter('ltruncate', default=None)

    @property
    @cached_result
    def truncate_path(self):
        """Обрезка пути с ограничением количества элементов пути"""
        return self._eval_parameter('truncate_path', default=None)

    @property
    @cached_result
    def ltruncate_path(self):
        """Обрезка пути слева"""
        return self._eval_parameter('ltruncate_path', default=None)

    @property
    @cached_result
    def truncate_to_parent(self):
        """Обрезка строки чтобы она вписалась в ширину парента"""
        return self._eval_parameter('truncate_to_parent', default=None)

    @property
    @cached_result
    def ltruncate_to_parent(self):
        """Обрезка строки слева чтобы она вписалась в ширину парента"""
        return self._eval_parameter('ltruncate_to_parent', default=None)

    @property
    @cached_result
    def title(self):
        """Применить функцию title()"""
        return self._eval_parameter('title', default=False)

    @property
    @cached_result
    def upper(self):
        """Применить функцию upper()"""
        return self._eval_parameter('upper', default=False)

    @property
    @cached_result
    def lower(self):
        """Применить функцию lower()"""
        return self._eval_parameter('lower', default=False)

    @property
    @cached_result
    def zfill(self):
        """Применить функцию zfill"""
        return self._eval_parameter('zfill', default=False)

    @property
    @cached_result
    def font(self):
        """
        Возвращает готовый шрифт для рендера
        """
        return ImageFont.truetype(self._resolve_font_name(self.font_name), self.font_size)

    def _resolve_font_name(self, font_name):
        """
        Поиск шрфита по имени

        Returns
        -------
        str
        """
        if not font_name.endswith('ttf'):
            font_name += '.ttf'
        # проверяем указан ли абсолютный путь
        if os.path.exists(font_name):
            return font_name
        # проверяем в кастомных директориях ресурсов
        search_paths = self.variables.get('local_resource_paths')
        if search_paths:
            for path in search_paths:
                font_1 = os.path.join(path, font_name)
                if os.path.exists(font_1):
                    return font_1
                font_2 = os.path.join(path, 'fonts', font_name)
                if os.path.exists(font_2):
                    return font_2
        # ищем в дефолтных шрифтах
        font_3 = os.path.join(self.default_fonts_dir, font_name)
        if os.path.exists(font_3):
            return font_3
        # пробуем достать из стандартных шрифтов системы
        try:
            ImageFont.truetype(font_name, 10)
            # шрфит найден
            return font_name
        except OSError:
            pass
        raise LookupError('Font {} not found'.format(font_name))

    @property
    @cached_result
    def font_name(self):
        """
        Путь к шрифту или имя шрифта из стандартных директорий
        """
        f = self._eval_parameter('font_name', default=None)
        return f or self.default_font_name

    @property
    @cached_result
    def default_font_name(self):
        """
        Путь или имя шрифта по умолчанию
        """
        default_name = self._eval_parameter('default_font_name', default=None) or self._default_font_name
        df = self._eval_parameter('default_font', default=None)
        if not df:
            df = default_name
        return df

    @property
    @cached_result
    def color(self):
        """Цвет текста"""
        clr = self._eval_parameter('text_color')
        if isinstance(clr, list):
            clr = tuple(clr)
        return clr

    @property
    @cached_result
    def outline(self):
        """Добавить обводку"""
        return self._eval_parameter('outline', default={})

    @property
    @cached_result
    def backdrop(self):
        """Добавить бекдроп (подложка)"""
        return self._eval_parameter('backdrop', default=None)

    @property
    @cached_result
    def fit_to_parent(self):
        """Вписать строку в ширину парента с переносом на новую строку"""
        return bool(self._eval_parameter('fit_to_parent', default=False))

    @property
    @cached_result
    def line_splitter(self):
        """Символ для разделения строки при переносе на новую строку"""
        return self._eval_parameter('line_splitter', default=None)

    @property
    @cached_result
    def move_splitter_to_next_line(self):
        """Определяет где будет оставаться символ-разделитель. но текущей строке или на новой"""
        return self._eval_parameter('move_splitter_to_next_line', default=None)

    @property
    @cached_result
    def max_lines_count(self):
        """Ограничение по количеству переходов на новую строку. После этого строка обрезается"""
        return self._eval_parameter('max_lines_count', default=None)

    @property
    @cached_result
    def lmax_lines_count(self):
        """Ограничение по уколичеству переходов на новую строку. Строка обрезается с начала"""
        return self._eval_parameter('lmax_lines_count', default=None)

    @property
    @cached_result
    def format_date(self):
        return self._eval_parameter('format_date', default=False)

    def get_font_metrics(self):
        (_, font_height), (_, offset_y) = self.font.font.getsize('A')
        return dict(
            font_height=font_height,
            offset_y=offset_y
        )

    @cached_result
    def get_size(self):
        """
        Размер текста в пикселях

        Returns
        -------
        (x,y): tuple
        """
        # общая высота текста без учета элементов под бейзлойном
        text_height = ((self.get_font_metrics()['font_height']+self.spacing)
                       * len(self.text.split('\n'))) - self.spacing
        # общая ширина текста по самой длинной строке
        text_width = max([self.font.getsize(text)[0] for text in self.text.split('\n')])
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
