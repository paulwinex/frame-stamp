import pytest
from PIL import Image

from frame_stamp.shape import ImageShape
from frame_stamp.utils.point import Point



# HELPERS


@pytest.fixture
def temp_png(tmp_path):
    img = Image.new("RGBA", (100, 50), (255, 0, 0, 255))
    path = tmp_path / "test.png"
    img.save(path)
    return path


@pytest.fixture
def temp_mask(tmp_path):
    img = Image.new("L", (100, 50), 128)
    path = tmp_path / "mask.png"
    img.save(path)
    return path


@pytest.fixture
def image_context(context, tmp_path):
    # allow resource loading
    context["resource_path"] = tmp_path
    return context


# SOURCE LOADING


def test_image_source_from_file(image_context, temp_png):
    shape_data = {
        "source": str(temp_png),
    }

    shape = ImageShape(shape_data, image_context)
    img = shape.source

    assert isinstance(img, Image.Image)
    assert img.size == (100, 50)


def test_image_source_missing_raises(image_context):
    shape_data = {
        "source": "no_such_file.png",
    }

    shape = ImageShape(shape_data, image_context)
    with pytest.raises(IOError):
        _ = shape.source


# BASE64 SOURCE

def test_image_source_base64(image_context, temp_png):
    from frame_stamp.utils.b64 import file_to_b64_value

    b64_value = file_to_b64_value(str(temp_png))

    shape_data = {
        "source": b64_value,
    }

    shape = ImageShape(shape_data, image_context)
    img = shape.source

    assert isinstance(img, Image.Image)
    assert img.size == (100, 50)


# SIZE / KEEP ASPECT

def test_image_original_size(image_context, temp_png):
    shape = ImageShape({"source": str(temp_png)}, image_context)
    assert shape.size == (100, 50)


def test_image_width_only_keep_aspect(image_context, temp_png):
    shape_data = {
        "source": str(temp_png),
        "width": 200,
        "keep_aspect": True,
    }

    shape = ImageShape(shape_data, image_context)
    assert shape.width == 200
    assert shape.height == 100


def test_image_height_only_keep_aspect(image_context, temp_png):
    shape_data = {
        "source": str(temp_png),
        "height": 200,
        "keep_aspect": True,
    }

    shape = ImageShape(shape_data, image_context)
    assert shape.height == 200
    assert shape.width == 400


def test_image_no_keep_aspect(image_context, temp_png):
    shape_data = {
        "source": str(temp_png),
        "width": 200,
        "height": 200,
        "keep_aspect": False,
    }

    shape = ImageShape(shape_data, image_context)
    assert shape.size == (200, 200)


def test_source_resized(image_context, temp_png):
    shape_data = {
        "source": str(temp_png),
        "width": 50,
        "height": 50,
    }

    shape = ImageShape(shape_data, image_context)
    img = shape.source_resized

    assert img.size == (50, 50)


# MASK & TRANSPARENCY


def test_mask_applied(image_context, temp_png, temp_mask):
    shape_data = {
        "source": str(temp_png),
        "mask": str(temp_mask),
    }

    shape = ImageShape(shape_data, image_context)
    img = shape.source

    assert img.mode == "RGBA"


def test_transparency_applied(image_context, temp_png):
    shape_data = {
        "source": str(temp_png),
        "transparency": 0.5,
    }

    shape = ImageShape(shape_data, image_context)
    img = shape.source

    assert img.mode == "RGBA"


@pytest.mark.parametrize("value,expected", [
    (-1, 0),
    (0, 0),
    (0.5, 0.5),
    (1, 1),
    (2, 1),
])
def test_transparency_clamped(image_context, temp_png, value, expected):
    shape_data = {
        "source": str(temp_png),
        "transparency": value,
    }

    shape = ImageShape(shape_data, image_context)
    assert shape.transparency == expected


# MULTIPLY COLOR


def test_multiply_color_rgb_tuple(image_context, temp_png):
    shape_data = {
        "source": str(temp_png),
        "multiply_color": (255, 128, 64),
    }

    shape = ImageShape(shape_data, image_context)
    assert shape.multiply_color == (255, 128, 64)


def test_multiply_color_rgb_string(image_context, temp_png):
    shape_data = {
        "source": str(temp_png),
        "multiply_color": "rgb(10,20,30)",
    }

    shape = ImageShape(shape_data, image_context)
    assert shape.multiply_color == (10, 20, 30)


def test_multiply_color_hsv_string(image_context, temp_png):
    shape_data = {
        "source": str(temp_png),
        "multiply_color": "hsv(0,255,255)",
    }

    shape = ImageShape(shape_data, image_context)
    assert isinstance(shape.multiply_color, tuple)
    assert len(shape.multiply_color) == 3


def test_multiply_color_invalid_string(image_context, temp_png):
    shape_data = {
        "source": str(temp_png),
        "multiply_color": "bad(1,2,3)",
    }

    shape = ImageShape(shape_data, image_context)
    with pytest.raises(ValueError):
        _ = shape.multiply_color


# DRAW SHAPE (SMOKE TEST)


def test_draw_shape_smoke(image_context, temp_png):
    shape_data = {
        "source": str(temp_png),
        "x": 10,
        "y": 20,
    }

    shape = ImageShape(shape_data, image_context)

    canvas = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    shape.draw_shape(
        shape_canvas=canvas,
        canvas_size=(300, 300),
        center=Point(0, 0),
        zero_point=Point(10, 20),
    )

    # no exception = success
    assert True
