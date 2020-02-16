# Frame Stamp

Пакет для добавления информации на кадры используя шаблон и контекст с переменными.


Быстрый пример:

```python

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

- реализация паддинга для grid

- вкл\выкл debug_shape через диалог

- прозрачность картинки работает некорректно

- маска артинки
