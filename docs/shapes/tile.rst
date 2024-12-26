Tile
----

    `inherited (BaseShape)`

Паттерн из других фигур.

tile_width
    Ширина плитки

tile_height
    Высота плитки

rotate
    Не используется. Можно повернуть направление сетки с помощью `grid_rotate`

grid_rotate
    Наклон сетки плиток в градусах

spacing
    Горизонтальное и вертикальное расстояние между плитками в виде списка

vertical_spacing
    Вертикалльное расстояние между плитками. Оверрайдит `spacing[0]`

horizontal_spacing:
    Горизонтальное расстояние между плитками. Оверайдит `spacing[1]`

row_offset
    Смещение строк через одну

column_offset
    Смещение столбцов через один

random_order
    Случайный порядок вложенных фигур

random_seed
    Сид для рандома


tile_index
    Значение доступно как локальная переменная. Содержит индекс текущей плитки.

Фигура `Tile` может иметь параметр `shapes` с вложенными фигурами.
Вложенные фигуры используются для замощения всего изображения.
Если вложенных фигур несколько то они циклично чередуются по порядку.

Каждая фигура имеет своего парента в виде основной зоны плитки и может быть трансформирована относительно него

.. code-block:: json

  {"templates":[
      {
      "defaults": {
          "font_size": "4p",
          "text1_color": [255, 0, 255, 100],
          "text2_color": [255, 255, 0, 100]
        },
        "variables": {
          "studio_name": "MyStudio"
        },
        "shapes": [
          {
              "type": "tile", "grid_rotate": -45,
              "tile_width": 250, "tile_height": 150,
              "row_offset": 250,
              "shapes":[
                  {
                      "type": "label", "text": "$studio_name", "text_color": "$text1_color",
                      "align_h": "center", "align_v": "center", "font_size": "$font_size"
                  },{
                      "type": "label", "text": "DEMO", "text_color": "$text2_color",
                      "align_h": "center", "align_v": "center", "font_size": "$font_size"
                  }
              ]
          }
        ]
      }
  ]
  }
