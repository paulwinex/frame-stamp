import pytest
from PIL import Image

from frame_stamp.shape.tile import TileShape
from frame_stamp.shape.rect import RectShape
from frame_stamp.utils.exceptions import PresetError
from frame_stamp.utils.point import Point


def test_tile_basic_init(context):
    shape = TileShape(
        {
            "shapes": [
                {"type": "rect", "width": 10, "height": 10},
            ]
        },
        context,
    )

    assert shape.shape_name == "tile"
    assert len(shape._shapes) == 1


def test_tile_rotate_always_zero(context):
    shape = TileShape(
        {
            "rotate": 90,
            "shapes": [{"type": "rect"}],
        },
        context,
    )

    assert shape.rotate == 0

def test_tile_inner_shape_id_forbidden(context):
    with pytest.raises(PresetError):
        TileShape(
            {
                "shapes": [
                    {"type": "rect", "id": "bad_id"}
                ]
            },
            context,
        )


def test_tile_iter_shapes_cycle(context):
    shape = TileShape(
        {
            "shapes": [
                {"type": "rect", "width": 10},
                {"type": "rect", "width": 20},
            ]
        },
        context,
    )

    it = shape.iter_shapes()
    s1 = next(it)
    s2 = next(it)
    s3 = next(it)

    assert s1 is shape._shapes[0]
    assert s2 is shape._shapes[1]
    assert s3 is shape._shapes[0]


def test_tile_generate_coords_basic(context):
    shape = TileShape(
        {
            "tile_width": 50,
            "tile_height": 50,
            "shapes": [{"type": "rect"}],
        },
        context,
    )

    coords = shape.generate_coords(
        rect_size=(200, 200),
        tile_size=(50, 50),
        spacing=(0, 0),
        pivot=(0, 0),
    )

    assert coords
    assert all(len(c) == 2 for c in coords)


def test_tile_generate_coords_with_spacing(context):
    shape = TileShape(
        {
            "tile_width": 50,
            "tile_height": 50,
            "spacing": (10, 20),
            "shapes": [{"type": "rect"}],
        },
        context,
    )

    coords = shape.generate_coords(
        rect_size=(200, 200),
        tile_size=(50, 50),
        spacing=(10, 20),
        pivot=(0, 0),
    )

    xs = sorted(set(x for x, _ in coords))
    ys = sorted(set(y for _, y in coords))

    assert xs[1] - xs[0] >= 50
    assert ys[1] - ys[0] >= 50


def test_tile_generate_coords_limits(context):
    shape = TileShape(
        {
            "tile_width": 50,
            "tile_height": 50,
            "max_rows": 2,
            "max_columns": 3,
            "shapes": [{"type": "rect"}],
        },
        context,
    )

    coords = shape.generate_coords(
        rect_size=(500, 500),
        tile_size=(50, 50),
        pivot=(0, 0),
        max_rows=2,
        max_columns=3,
    )

    # 2 * 3 tiles максимум
    assert len(coords) <= 6

def test_tile_generate_coords_zero_tile_size(context):
    shape = TileShape(
        {
            "tile_width": 0,
            "tile_height": 50,
            "shapes": [{"type": "rect"}],
        },
        context,
    )

    with pytest.raises(ValueError):
        shape.generate_coords(
            rect_size=(100, 100),
            tile_size=(0, 50),
        )


def test_tile_render_smoke(context):
    parent = RectShape(
        {
            "x": 0,
            "y": 0,
            "width": 200,
            "height": 200,
        },
        context,
    )

    tile = TileShape(
        {
            "tile_width": 40,
            "tile_height": 40,
            "shapes": [
                {
                    "type": "rect",
                    "width": 20,
                    "height": 20,
                    "color": "black",
                }
            ]
        },
        context,
    )

    tile.set_parent(parent)

    canvas = Image.new("RGBA", (200, 200), (255, 255, 255, 0))
    results = list(tile.render(canvas.size))

    # либо что-то отрисовалось, либо пусто — главное, что не упало
    assert isinstance(results, list)
