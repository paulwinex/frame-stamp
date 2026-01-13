import pytest

from frame_stamp.shape.base_shape import RootParent
from frame_stamp.utils.point import Point


def test_shape_basic_identity(rect_shape):
    assert rect_shape.id == "rect1"
    assert rect_shape.shape_name == "rect"


def test_parent_is_root(rect_shape):
    assert isinstance(rect_shape.parent, RootParent)


def test_scope_excludes_self(rect_shape):
    assert rect_shape.id not in rect_shape.scope


def test_source_image_access(rect_shape):
    img = rect_shape.source_image
    assert img.size == (400, 300)


def test_unit_and_point(rect_shape):
    assert rect_shape.unit == pytest.approx(3.0)  # 1% of height = 300
    assert rect_shape.point > 0


def test_width_height(rect_shape):
    assert rect_shape.width == 100
    assert rect_shape.height == 50


def test_position(rect_shape):
    assert rect_shape.x == 10
    assert rect_shape.y == 20
    assert rect_shape.pos == Point(10, 20)


def test_bounds(rect_shape):
    assert rect_shape.x0 == 10
    assert rect_shape.y0 == 20
    assert rect_shape.x1 == 110
    assert rect_shape.y1 == 70


def test_center(rect_shape):
    assert rect_shape.center_x == 60
    assert rect_shape.center_y == 45


def test_alignment_defaults(rect_shape):
    assert rect_shape.align_h is None
    assert rect_shape.align_v is None


def test_color_from_defaults(rect_shape):
    assert rect_shape.color == (255, 0, 0, 255)


def test_rotation_defaults(rect_shape):
    assert rect_shape.rotate == 0
    assert rect_shape.global_rotate == 0


def test_rotation_pivot_default(rect_shape):
    pivot = rect_shape.rotation_pivot
    assert isinstance(pivot, Point)
    assert pivot == rect_shape.center


def test_skip_default(rect_shape):
    assert rect_shape.skip is False


def test_enabled_default(rect_shape):
    assert rect_shape.is_enabled() is True


def test_z_index(rect_shape):
    assert rect_shape.z_index == 0


def test_raw_rect(rect_shape):
    rect = rect_shape.raw_rect
    assert rect.width == 100
    assert rect.height == 50


def test_gradient_default(rect_shape):
    assert rect_shape.gradient is None
