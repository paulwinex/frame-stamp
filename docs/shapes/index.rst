.. _shapes:

Фигуры
------

Здесь перечислены все доступные фигуры. Каждая фигура имеет своё представление в рендере.
Все они наследуются от базовой фигуры, наследуя её параметры и поля.

Параметры
=========

Это аргументы, которые можно задать в шаблоне, они влияют на то как фигура будет рендериться.

Пример: создание фигуры  с заданием параметров.

.. code-block:: json

    {
        "type": "shape-type", "x": 0, "y": 0,
        "parameter": "value"
    }

Поля
====

Это атрибуты фигуры, доступные в шаблоне для получения определённых данных.

Многие поля являются параметрами, которые заданы при создании фигуры, но есть
и те, которые рассчитываются автоматически и доступны в шаблоне.

Например, указав позицию и размер фигуры, мы получаем поле ``left``, возвращающее самую левую
точку фигуры в глобальных координатах.

Пример: вторая фигура ссылается на поле ``left`` первой фигуры. Это позволяет создать зависимость между положением фигур.

.. code-block:: json

    {
        "shapes":[
            {
                "type": "rect", "x":0, "y": 100, "id": "shape1",
                "width": 100, "height": 100
            },
            {
                "type": "rect", "x": 0, "y": "shape1.left",
                "width": 100, "height": 100
            }
        ]
    }

.. note:: Все указанные параметры доступны в шаблоне под теми же именами

Далее в документации будут указаны доступные **параметры** и **поля** для каждой фигуры.

.. note:: Фигура наследует все параметры и поля родительской фигуры.
          В документации будут указаны только новые для этого класса параметры и поля

Список доступных фигур
======================

.. toctree::
   :maxdepth: 1

   base_shapes
   rect
   label
   image
   line
   tile
   grid
   row
   column
