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
make install
```

### Open UI

```shell
make run 
```
