import pytest

from frame_stamp.shape import GridShape, LabelShape
from frame_stamp.utils.exceptions import PresetError


# BASIC GRID CREATION

def test_empty_grid(context):
    shape = GridShape({}, context)
    assert shape.get_cell_shapes() == []


def test_grid_without_shapes(context):
    shape = GridShape({"shapes": []}, context)
    assert shape.get_cell_shapes() == []


def test_grid_shape_name(context):
    shape = GridShape({}, context)
    assert shape.shape_name == "grid"


# ROWS / COLUMNS

def test_grid_fixed_rows_columns(context):
    shape_data = {
        "width": 200,
        "height": 100,
        "rows": 2,
        "columns": 2,
        "shapes": [
            {"type": "rect"},
            {"type": "rect"},
            {"type": "rect"},
            {"type": "rect"},
        ]
    }

    grid = GridShape(shape_data, context)
    cells = grid.generate_cells(4)

    assert len(cells) == 4
    assert {c["row"] for c in cells} == {0, 1}
    assert {c["column"] for c in cells} == {0, 1}


def test_grid_auto_columns(context):
    shape_data = {
        "width": 300,
        "height": 100,
        "rows": 1,
        "columns": "auto",
        "shapes": [
            {"type": "rect"},
            {"type": "rect"},
            {"type": "rect"},
        ]
    }

    grid = GridShape(shape_data, context)
    cells = grid.generate_cells(3)

    assert max(c["column"] for c in cells) == 2
    assert max(c["row"] for c in cells) == 0


def test_grid_auto_rows(context):
    shape_data = {
        "width": 300,
        "height": 300,
        "rows": "auto",
        "columns": 2,
        "shapes": [
            {"type": "rect"},
            {"type": "rect"},
            {"type": "rect"},
            {"type": "rect"},
        ]
    }

    grid = GridShape(shape_data, context)
    cells = grid.generate_cells(4)

    assert max(c["row"] for c in cells) == 1


# PADDING & SPACING

def test_grid_padding(context):
    shape_data = {
        "width": 200,
        "height": 200,
        "padding": 10,
        "rows": 1,
        "columns": 1,
        "shapes": [{"type": "rect"}]
    }

    grid = GridShape(shape_data, context)
    cells = grid.generate_cells(1)

    cell = cells[0]
    assert cell["x"] == 10
    assert cell["y"] == 10


def test_grid_horizontal_vertical_spacing(context):
    shape_data = {
        "width": 300,
        "height": 100,
        "rows": 1,
        "columns": 3,
        "horizontal_spacing": 10,
        "shapes": [
            {"type": "rect"},
            {"type": "rect"},
            {"type": "rect"},
        ]
    }

    grid = GridShape(shape_data, context)
    cells = grid.generate_cells(3)

    assert cells[1]["x"] > cells[0]["x"]
    assert cells[2]["x"] > cells[1]["x"]


# COLUMNS WIDTH

def test_grid_columns_width_override(context):
    shape_data = {
        "width": 300,
        "height": 100,
        "rows": 1,
        "columns": 3,
        "columns_width": {
            "0": 50,
            "-1": 100,
        },
        "shapes": [
            {"type": "rect"},
            {"type": "rect"},
            {"type": "rect"},
        ]
    }

    grid = GridShape(shape_data, context)
    cells = grid.generate_cells(3)

    assert cells[0]["width"] == 50
    assert cells[2]["width"] == 100


def test_grid_columns_width_negative_index_out_of_range(context):
    shape_data = {
        "width": 200,
        "height": 100,
        "rows": 1,
        "columns": 2,
        "columns_width": {
            "-3": 50,  # ignored
        },
        "shapes": [
            {"type": "rect"},
            {"type": "rect"},
        ]
    }

    grid = GridShape(shape_data, context)
    cells = grid.generate_cells(2)

    assert all(c["width"] > 0 for c in cells)


# CELL SHAPES CREATION

def test_grid_creates_child_shapes(context):
    shape_data = {
        "width": 200,
        "height": 100,
        "rows": 1,
        "columns": 2,
        "shapes": [
            {"type": "label", "text": "A"},
            {"type": "label", "text": "B"},
        ]
    }

    grid = GridShape(shape_data, context)
    shapes = grid.get_cell_shapes()

    assert len(shapes) == 2
    assert all(isinstance(s, LabelShape) for s in shapes)
    assert shapes[0]._local_context["column"] == 0
    assert shapes[1]._local_context["column"] == 1


def test_grid_skip_shape(context):
    shape_data = {
        "width": 200,
        "height": 100,
        "rows": 1,
        "columns": 2,
        "shapes": [
            {"type": "label", "text": "A"},
            {"type": "label", "text": "B", "skip": True},
        ]
    }

    grid = GridShape(shape_data, context)
    shapes = grid.get_cell_shapes()

    assert len(shapes) == 1
    assert shapes[0].text == "A"


def test_grid_duplicate_shape_id_raises(context):
    shape_data = {
        "width": 200,
        "height": 100,
        "rows": 1,
        "columns": 2,
        "shapes": [
            {"type": "rect", "id": "x"},
            {"type": "rect", "id": "x"},
        ]
    }

    with pytest.raises(PresetError):
        GridShape(shape_data, context)


# FIT TO CONTENT HEIGHT

def test_grid_fit_to_content_height(context):
    shape_data = {
        "width": 200,
        "height": 50,
        "rows": 1,
        "columns": 2,
        "fit_to_content_height": True,
        "shapes": [
            {"type": "label", "text": "SHORT"},
            {"type": "label", "text": "THIS IS A VERY VERY LONG TEXT"},
        ]
    }

    grid = GridShape(shape_data, context)
    shapes = grid.get_cell_shapes()

    heights = [s.parent.height for s in shapes]
    assert heights[0] == heights[1]


# BORDER

def test_grid_border_defaults(context):
    shape_data = {
        "border": {},
    }

    grid = GridShape(shape_data, context)
    assert grid.border["enabled"] is True
    assert grid.border["width"] == 1
    assert grid.border["color"] == "black"


def test_grid_border_custom(context):
    shape_data = {
        "border": {
            "width": 3,
            "color": [255, 0, 0],
            "enabled": False,
        }
    }

    grid = GridShape(shape_data, context)
    assert grid.border["enabled"] is False
    assert grid.border["width"] == 3
    assert grid.border["color"] == (255, 0, 0)


# ROTATION (NOT SUPPORTED)

def test_grid_rotation_is_ignored(context):
    shape_data = {
        "rotate": 45,
    }

    grid = GridShape(shape_data, context)
    assert grid.rotate == 0
