from __future__ import absolute_import
from .base_shape import BaseShape
from PIL import ImageFont
import string


class LabelShape(BaseShape):
    """
    Текст

    Allowed parameters:
        x                  : Координата Х
        y                  : Координата У
        text               : Текст. Поддерживается форматирование переменных их конеткста "Project: $project_name"
        text_color         : Цвет текста
        text_spacing       : Расстояние между строк в многосточном тексте. По умолчанию 0
        font_size          : Размер шрифта
        font_name          : Используемый шрифт
        text_margin        : Отступ текста от указанных координат
        bound:  (100, 0)   : Допустимый объем для текста TODO
        alight_x           : Выравнивание относительно координаты X (left, right, center)
        alight_y           : Выравнивание относительно координаты X (top, bottom, center)
        align              : Выравнивание строк между собой для многострочного текста
        parent             : Родительский объект
    """
    shape_name = 'label'

    @property
    def x(self):
        x = super(LabelShape, self).x
        x_size, _ = self.get_size()
        align_x = self.align_x
        if align_x:
            if align_x not in ['left', 'right', 'center']:
                raise ValueError('Align X value must be only left, right or center')
            if align_x == 'left':
                pass    # default
            elif align_x == 'right':
                x -= x_size
            else:
                x -= x_size//2
        return x

    @property
    def y(self):
        y = super(LabelShape, self).y
        _, y_size = self.get_size()
        align_y = self.align_y
        if align_y:
            if align_y not in ['top', 'bottom', 'center']:
                raise ValueError('Align Y value must be only top, bottom or center')
            if align_y == 'top':
                pass  # default
            elif align_y == 'bottom':
                y -= y_size
            else:
                y -= y_size // 2
        return y

    @property
    def align_x(self):
        return self._eval_parameter('align_x', default=None)

    @property
    def align_y(self):
        return self._eval_parameter('align_y', default=None)

    @property
    def align(self):
        return self._eval_parameter('align', default='left')

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

    @property
    def text_margin(self):
        return self._eval_parameter('text_margin')

    def get_size(self):
        """
        Размер текста в пикселях

        Returns
        -------
        tuple
        """
        return self.font.getsize(self.text)

    @property
    def width(self):
        return self.get_size()[0]

    @property
    def height(self):
        return self.get_size()[1]

    def render(self, img, **kwargs):
        bound = self.bound
        is_multiline = '\n' in self.text
        printer = img.multiline_text if is_multiline else img.text
        text_args = dict(
            font=self.font,
            fill=self.text_color
        )
        if is_multiline:
            text_args['spacing'] = self.spacing
            text_args['align'] = self.align
        if bound:
            pass
            # todo: не реализовано!
            # import textwrap
            # margin = offset = 40
            # for line in textwrap.wrap(self.text, width=40):
            #     printer((margin, offset), line, **text_args)
            #     offset += self.font.getsize(line)[1]
        else:
            printer((self.x+self.text_margin, self.y+self.text_margin), self.text, **text_args)


