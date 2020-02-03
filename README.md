# Frame Stamp

Пакет для добавления информации на кадры используя шаблон и контекст с переменными.


Быстрый пример:

```python
# создаём инстанс изображения из библиотеки PIL
src_img = Image.open(img_path)
# Шаблон стампинга
template = {...}
# контекст с переменными
context = {...}
# инстанс рендерилки
renderer = FrameStamp(template, context)
# рендер кадра
stamped_img = renderer.render(img)
# сохранение результата
stamped_img.save(output_path, 'JPG')
```
