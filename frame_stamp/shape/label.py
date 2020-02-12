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
        color              : Цвет текста
        text_spacing       : Расстояние между строк в многосточном тексте. По умолчанию 0
        font_size          : Размер шрифта
        font_name          : Используемый шрифт
        text_margin        : Отступ текста от указанных координат
        margin_top         : Дополнительный отступ сверху
        margin_left        : Дополнительный отступ слева
        bound              : Допустимый объем для текста
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
        margin = self.margin_left
        t_margin = self.text_margin
        if align_x:
            margin = 0
            if align_x not in ['left', 'right', 'center']:
                raise ValueError('Align X value must be only left, right or center')
            if align_x == 'left':
                pass    # default
            elif align_x == 'right':
                b = self.bound
                if b:
                    x = x+b[0] - x_size
                else:
                    x -= x_size
            else:   # center
                t_margin = 0
                b = self.bound
                if b:
                    x = x + b[0]//2 - x_size//2
                else:
                    x -= x_size//2
        return x+margin+t_margin

    @property
    def y(self):
        y = super(LabelShape, self).y
        _, y_size = self.get_size()
        align_y = self.align_y
        margin = self.margin_top
        t_margin = self.text_margin
        if align_y:
            margin = 0
            if align_y not in ['top', 'bottom', 'center']:
                raise ValueError('Align Y value must be only top, bottom or center')
            if align_y == 'top':
                pass  # default
            elif align_y == 'bottom':
                b = self.bound
                if b:
                    y = y+b[1]-y_size
                else:
                    y -= y_size
            else:   # center
                t_margin = 0
                b = self.bound
                if b:
                    y = y + (b[1]//2) - y_size//2
                else:
                    y -= y_size // 2
        return y+margin+t_margin

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
        text = self._data['text']
        if '$' in text:
            text = string.Template(text).substitute(**self.context)
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
    def bound(self) -> list:
        """
        Ограничение размера текста

        Returns
        -------
        tuple
        """
        bound = self._eval_parameter('bound', default=None)
        if bound:
            return [self._eval_parameter_convert('bound', x) for x in bound]
        else:
            return []

    @property
    def color(self):
        return self._eval_parameter('text_color')

    @property
    def text_margin(self):
        return self._eval_parameter('text_margin')

    @property
    def margin_top(self):
        return self._eval_parameter('margin_top', default=0)

    @property
    def margin_left(self):
        return self._eval_parameter('margin_left', default=0)

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
            if self.align_x:
                text_args['align'] = self.align_x
        printer((self.x, self.y+self.text_margin), self.text, **text_args)
        return img




