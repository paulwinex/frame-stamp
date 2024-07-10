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
    if is_b64(base64_str):
        data = value_to_data(base64_str)
        base64_str = data['data']
    file = base64.b64decode(base64_str)
    return BytesIO(file)


def b64_str_to_image(base64_str: str):
    image_stream = b64_str_to_file(base64_str)
    return Image.open(image_stream)
