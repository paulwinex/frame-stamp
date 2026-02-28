from PIL import Image

from frame_stamp.shape.line import LineShape
from frame_stamp.utils.point import Point


# BASIC PROPERTIES


def test_line_points_default(context):
    shape = LineShape({}, context)

    assert shape.points == []


def test_line_thickness_default(context):
    shape = LineShape({}, context)

    assert shape.thickness == LineShape.default_width


def test_line_joints_default(context):
    shape = LineShape({}, context)

    assert shape.joints is True


# WIDTH / HEIGHT


def test_line_width_height_from_points(context):
    shape = LineShape(
        {
            "points": [
                [0, 0],
                [10, 5],
                [7, 20],
            ]
        },
        context
    )

    assert shape.width == 10
    assert shape.height == 20


def test_line_width_height_empty(context):
    shape = LineShape({}, context)

    assert shape.width == 0
    assert shape.height == 0


# DRAWING


def test_line_draw_basic(context):
    shape = LineShape(
        {
            "points": [[0, 0], [20, 0]],
            "thickness": 4,
            "color": "black",
        },
        context,
    )

    canvas = Image.new("RGBA", (50, 20), (255, 255, 255, 0))
    shape.draw_shape(
        shape_canvas=canvas,
        canvas_size=canvas.size,
        center=Point(0, 0),
        zero_point=Point(0, 10),
    )
    assert canvas.getbbox() is not None
    assert canvas.getbbox() == (0, 9, 22, 13)


def test_line_draw_with_joints(context):
    shape = LineShape(
        {
            "points": [[0, 0], [10, 10], [20, 0]],
            "thickness": 6,
            "joints": True,
            "color": "black",
        },
        context,
    )

    canvas = Image.new("RGBA", (40, 40), (255, 255, 255, 0))
    shape.draw_shape(
        shape_canvas=canvas,
        canvas_size=canvas.size,
        center=Point(0, 0),
        zero_point=Point(10, 10),
    )

    assert canvas.getbbox() is not None


def test_line_draw_without_joints(context):
    shape = LineShape(
        {
            "points": [[0, 0], [10, 10], [20, 0]],
            "thickness": 6,
            "joints": False,
            "color": "black",
        },
        context,
    )

    canvas = Image.new("RGBA", (40, 40), (255, 255, 255, 0))
    shape.draw_shape(
        shape_canvas=canvas,
        canvas_size=canvas.size,
        center=Point(0, 0),
        zero_point=Point(10, 10),
    )

    assert canvas.getbbox() is not None


# PARAMETER CONVERSION


def test_line_points_expression_conversion(context):
    shape = LineShape(
        {
            "points": [
                ["`=10+5`", "`=5*2`"],
                ["20", "30"],
            ],
        },
        context,
    )

    canvas = Image.new("RGBA", (50, 50), (0, 0, 0, 0))
    shape.draw_shape(
        shape_canvas=canvas,
        canvas_size=canvas.size,
        center=Point(0, 0),
        zero_point=Point(0, 0),
    )

    assert canvas.getbbox() is not None
    assert canvas.getbbox() == (15, 10, 22, 31)
