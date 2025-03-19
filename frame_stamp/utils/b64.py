from io import BytesIO
import base64
from pathlib import Path

from PIL import Image


def value_to_data(value) -> [str, str]:
    if value.startswith('base64::'):
        _, filename, data = value.split('::', 2)
        return dict(
            data=data,
            filename=filename
        )


def is_b64(value: str) -> bool:
    return value.startswith('base64::')


def file_to_b64_value(file_path: str):
    with open(file_path, 'rb') as f:
        base64_str = base64.b64encode(f.read()).decode('utf-8')
    return f'base64::{Path(file_path).name}::{base64_str}'


def file_to_b64_str(file_path: str):
    with open(file_path, 'rb') as f:
        base64_str = base64.b64encode(f.read()).decode('utf-8')
    return base64_str


def b64_str_to_file(base64_str: str):
    if not is_b64(base64_str):
        raise ValueError('Not a base64 string')
    data = value_to_data(base64_str)
    base64_str = data['data']
    file = base64.b64decode(base64_str)
    return BytesIO(file)


def b64_to_file(base64_str: str, image_size: tuple = None):
    if not is_b64(base64_str):
        raise ValueError('Not a base64 string')
    data = value_to_data(base64_str)
    base64_str = data['data']
    filename = data['filename']
    file_data = base64.b64decode(base64_str)
    ext = Path(filename).suffix.lower()
    if ext in ('.jpg', '.jpeg', '.png'):
        file = Image.open(BytesIO(file_data))
    elif ext == '.svg':
        from .render_svg import render_svg
        file = render_svg(file_data.decode(), image_size)
    else:
        file = BytesIO(file_data)
    return file


def b64_str_to_image(base64_str: str):
    image_stream = base64.b64decode(base64_str)
    return Image.open(image_stream)


def b64_str_to_dict(base64_str: str, as_image=False):
    if not is_b64(base64_str):
        raise ValueError('Not a base64 string')
    data = value_to_data(base64_str)
    file_data = data['data']
    return dict(
        file=base64.b64decode(file_data),
        filename=data['filename']
    )