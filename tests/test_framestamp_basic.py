# tests/test_framestamp_basic.py
from frame_stamp.shape.base_shape import BaseShape


def test_framestamp_creates_shapes(framestamp):
    shapes = list(framestamp.get_shapes())
    assert len(shapes) == 1
    assert isinstance(shapes[0], BaseShape)


def test_scope_contains_shape(framestamp):
    assert "rect1" in framestamp.scope
    assert framestamp.scope["rect1"].id == "rect1"


def test_variables_merge(rect_template, framestamp):
    assert framestamp.variables == rect_template["variables"]


def test_defaults_accessible(rect_template, framestamp):
    assert framestamp.defaults == rect_template["defaults"]


def test_source_image_loaded(framestamp):
    img = framestamp.source
    assert img.size == (400, 300)
