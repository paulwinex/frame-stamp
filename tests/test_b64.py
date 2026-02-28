import base64
import io
import tempfile

import pytest
from pathlib import Path
from PIL import Image

from frame_stamp.utils import b64



# HELPERS


@pytest.fixture
def temp_png():
    img = Image.new("RGBA", (16, 8), (255, 0, 0, 255))
    path = Path(tempfile.gettempdir(), "test.png")
    img.save(path)
    return path



# BASIC DETECTION


def test_is_b64_true():
    value = "base64::test.png::AAAA"
    assert b64.is_b64(value) is True


def test_is_b64_false():
    assert b64.is_b64("AAAA") is False
    assert b64.is_b64("") is False



# VALUE PARSING


def test_value_to_data():
    value = "base64::image.png::ABCDEF"
    data = b64.value_to_data(value)

    assert data["filename"] == "image.png"
    assert data["data"] == "ABCDEF"



# FILE > BASE64


def test_file_to_b64_value(temp_png):
    value = b64.file_to_b64_value(str(temp_png))

    assert value.startswith("base64::test.png::")
    assert b64.is_b64(value)


def test_file_to_b64_str(temp_png):
    base64_str = b64.file_to_b64_str(str(temp_png))

    decoded = base64.b64decode(base64_str)
    assert isinstance(decoded, bytes)



# BASE64 > FILE / IMAGE


def test_b64_str_to_file(temp_png):
    value = b64.file_to_b64_value(str(temp_png))
    file = b64.b64_str_to_file(value)

    assert isinstance(file, io.BytesIO)
    assert file.getbuffer().nbytes > 0


def test_b64_to_file_image(temp_png):
    value = b64.file_to_b64_value(str(temp_png))
    img = b64.b64_to_file(value)

    assert isinstance(img, Image.Image)
    assert img.size == (16, 8)


def test_b64_to_file_invalid():
    with pytest.raises(ValueError):
        b64.b64_to_file("not_base64")



# BASE64 > IMAGE (RAW STRING)


def test_b64_str_to_image(temp_png):
    raw = b64.file_to_b64_str(str(temp_png))
    img = b64.b64_str_to_image(raw)

    assert isinstance(img, Image.Image)
    assert img.size == (16, 8)



# BASE64 > DICT


def test_b64_str_to_dict(temp_png):
    value = b64.file_to_b64_value(str(temp_png))
    data = b64.b64_str_to_dict(value)

    assert data["filename"] == "test.png"
    assert isinstance(data["file"], bytes)
    assert len(data["file"]) > 0


def test_b64_str_to_dict_invalid():
    with pytest.raises(ValueError):
        b64.b64_str_to_dict("not_base64")
