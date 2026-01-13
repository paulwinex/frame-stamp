import pytest
from datetime import datetime

from frame_stamp.shape import LabelShape, RectShape
from frame_stamp.shape.base_shape import BaseShape


# ------------------------------------------------------------------
# TEXT / VARIABLES / EXPRESSIONS
# ------------------------------------------------------------------

def test_label_variable_substitution(context):
    shape_data = {
        "text": "hello $value",
    }
    context["variables"]["value"] = 123

    shape = LabelShape(shape_data, context)
    assert shape.text == "hello 123"


def test_label_multiple_variable_substitution(context):
    shape_data = {
        "text": "$a + $b = `=$a+$b`",
    }
    context["variables"].update({
        "a": 2,
        "b": 3,
    })

    shape = LabelShape(shape_data, context)
    assert shape.text == "2 + 3 = 5"


def test_label_multiple_inline_expressions(context):
    shape_data = {
        "text": "`=$value1+$value2` and `=$value1-$value2`",
    }
    context["variables"].update({
        "value1": 2,
        "value2": 3,
    })

    shape = LabelShape(shape_data, context)
    assert shape.text == "5 and -1"


# ------------------------------------------------------------------
# EXPRESSIONS IN GEOMETRY (via BaseShape)
# ------------------------------------------------------------------

def test_expression_in_position(context):
    shape_data = {
        "x": "`=20+30`",
        "y": "`=self.x/2`",
    }

    shape = RectShape(shape_data, context)
    assert shape.x == 50
    assert shape.y == 25


def test_expression_with_variables(context):
    shape_data = {
        "x": "`=$xpos/2`",
    }
    context["variables"]["xpos"] = 200

    shape = RectShape(shape_data, context)
    assert shape.x == 100


# ------------------------------------------------------------------
# BASE SHAPE SANITY (for completeness)
# ------------------------------------------------------------------

def test_base_shape_position(context):
    shape_data = {
        "x": 200,
        "y": 300,
    }
    shape = BaseShape(shape_data, context)

    assert shape.x == 200
    assert shape.y == 300


# ------------------------------------------------------------------
# LABEL PROPERTIES
# ------------------------------------------------------------------

def test_label_basic_properties(context):
    shape_data = {
        "text": "hello",
        "font_name": "Monospace",
        "font_size": 20,
        "text_color": "red",
        "text_spacing": 10,

        "zfill": True,
        "lower": False,
        "upper": True,
        "title": False,

        "fit_to_parent": True,

        "outline": 4,

        "padding": 10,
        "padding_right": 11,
    }

    shape = LabelShape(shape_data, context)

    # text transforms
    assert shape.text == "HELLO"
    assert shape.lower is False
    assert shape.upper is True
    assert shape.title is False
    assert shape.zfill is True

    # font
    assert shape.font_name == "Monospace"
    assert shape.font_size == 20

    # color
    assert shape.color == "red"

    # spacing / padding
    assert shape.padding_left == 10
    assert shape.padding_top == 10
    assert shape.padding_bottom == 10
    assert shape.padding_right == 11

    # outline
    assert shape.outline == {"width": 4}

    # behavior flags
    assert shape.fit_to_parent is True


# ------------------------------------------------------------------
# TEXT TRANSFORMS
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    "params, expected",
    [
        ({"upper": True}, "HELLO"),
        ({"lower": True}, "hello"),
        ({"title": True}, "Hello"),
    ]
)
def test_label_case_transforms(context, params, expected):
    shape_data = {
        "text": "hello",
        **params,
    }

    shape = LabelShape(shape_data, context)
    assert shape.text == expected


# ------------------------------------------------------------------
# TRUNCATION
# ------------------------------------------------------------------

def test_label_truncate(context):
    shape_data = {
        "text": "ABCDEFG",
        "truncate": 4,
    }

    shape = LabelShape(shape_data, context)
    assert shape.text == "ABCD..."


def test_label_ltruncate(context):
    shape_data = {
        "text": "ABCDEFG",
        "ltruncate": 4,
    }

    shape = LabelShape(shape_data, context)
    assert shape.text == "...DEFG"


# ------------------------------------------------------------------
# DATE FORMATTING
# ------------------------------------------------------------------

def test_label_date_formatting(context):
    shape_data = {
        "text": "date: {:%Y/%m/%d}",
        "format_date": True,
    }

    context["variables"]["timestamp"] = datetime(
        year=2025, month=5, day=15
    ).timestamp()

    shape = LabelShape(shape_data, context)
    assert shape.text == "date: 2025/05/15"


# ------------------------------------------------------------------
# EDGE CASES
# ------------------------------------------------------------------

def test_label_empty_text(context):
    shape = LabelShape({"text": ""}, context)
    assert shape.text == ""


def test_label_no_text(context):
    shape = LabelShape({}, context)
    assert shape.text == ""


def test_label_non_string_text(context):
    shape = LabelShape({"text": 123}, context)
    assert shape.text == "123"

def test_label_expression_order(context):
    shape_data = {
        "x": 10,
        "text": "`=self.x*2`",
    }
    shape = LabelShape(shape_data, context)
    assert shape.text == "20"