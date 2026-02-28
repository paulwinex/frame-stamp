# tests/conftest.py
import json
import tempfile

import pytest
from pathlib import Path
from PIL import Image

from frame_stamp import FrameStamp

TEMPLATES_DIR = Path(__file__, '../templates').resolve()

@pytest.fixture
def simple_template():
    template_path = TEMPLATES_DIR / 'simple_template.json'
    with template_path.open() as f:
        return json.load(f)['templates'][0]

@pytest.fixture(scope='function')
def context(temp_image, simple_template):
    stamp = FrameStamp(temp_image, simple_template, {})
    return stamp._shared_context


@pytest.fixture
def temp_image() -> Path:
    """Временная тестовая картинка"""
    img_path = Path(tempfile.gettempdir(), "source.png")
    img = Image.new("RGB", (400, 300), color="white")
    img.save(img_path)
    return img_path


@pytest.fixture
def rect_template():
    """Минимальный шаблон с одной rect-формой"""
    return {
        "defaults": {
            "color": [255, 0, 0, 255],
            "w": 100,
            "h": 50,
        },
        "variables": {},
        "shapes": [
            {
                "type": "rect",
                "id": "rect1",
                "x": 10,
                "y": 20,
            }
        ]
    }


@pytest.fixture
def framestamp(temp_image, rect_template):
    return FrameStamp(
        image=temp_image,
        template=rect_template,
        variables={}
    )


@pytest.fixture
def rect_shape(framestamp):
    return next(framestamp.get_shapes())
