Создание новых форм
-------------------


Для создания новой формы следует выполнить следующие действия

1. Создать новый модуль в пакете ``frame_stamp.shape``

2. Создать класс, наследованный от ``frame_stamp.shape.base_shape.BaseShape``

3. Определить имя новой формы в атрибуте ``shape_name``

4. Определить метод ``draw_shape()`` для описания процесса рендера формы.

Метод ``draw_shape()`` принимает аргумент ``size``, и должен вернуть новый инстанс класса ``PIL.Image`` указанного размера
с формате ``RGBA``. Этот слой будет прикомпожен сверху к имеющейся картинке.

Для получения чистого слоя перед рендером используйте метод ``canvas = self._get_canvas(size)`` после чего можно рисовать на
этом слое.

.. note:: Движок использует библиотеку `Pillow` для рисования форм.

Пример
======

Ниже приведён пример создания новой формы. Эта форма рисует круги.

.. code-block:: python

    from .base_shape import BaseShape
    from PIL import ImageDraw

    class CircleShape(BaseShape):
        shape_name = 'circle'

        @property
        def radius(self):
            return self._eval_parameter('radius', default=0)

        def draw_shape(self, size, **kwargs):
            canvas = self._get_canvas(size)
            img = ImageDraw.Draw(canvas)
            img.ellipse((self.x-(self.radius/2),
                         self.y-(self.radius/2),
                         self.x+(self.radius/2),
                         self.y+(self.radius/2),), fill=self.color)
            return canvas

Теперь в шаблонах можно использовтаь новый тип формы ``circle`` с параметром ``radius``.

