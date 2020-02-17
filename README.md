# Frame Stamp

Пакет для добавления информации на кадры используя шаблон и контекст с переменными.


Быстрый пример:

```python
from frame_stamp.stamp import FrameStamp

input_file = '...'
output_file = '...'
# Шаблон стампинга
template = {}
# контекст с переменными
variables = {}
# инстанс рендерилки
fs = FrameStamp(input_file, template, variables)
# рендерим результат в другой файл
fs.render(save_path=output_file)
```


### TODO

- вкл\выкл debug_shape через диалог

- прозрачность картинки работает некорректно

- маска артинки

- выбор номера кадра или процента сиквенса для слейта

- разобраться с диапазоном кадров и номерами кадров в прожиге

- поворот шейпы во время рендера

- поддержка шаблонов в формате py

- выравнивание неполных строк и колонок
