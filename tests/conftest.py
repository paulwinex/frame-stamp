# tests/conftest.py
import pytest
from pathlib import Path
from PIL import Image

from frame_stamp import FrameStamp


@pytest.fixture
def temp_image(tmp_path: Path) -> Path:
    """Временная тестовая картинка"""
    img_path = tmp_path / "source.png"
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
