# Frame Stamp

A tool for render technical information over image using template with render context

Quick example:

```python
from frame_stamp.stamp import FrameStamp

input_file = '...'
output_file = '...'
# template for stamping
template = {}
# render context
variables = {}
# frame stamp instance
fs = FrameStamp(input_file, template, variables)
# render
fs.render(save_path=output_file)
```

### Initialize dev env

```shell
poetry install
```

### Open UI

```shell
make run 
```

### TODO

- alignment for grid
- add templates in yaml and py format
- limit column with
- fit ceil content
- Gradient fill
- Template Designer UI