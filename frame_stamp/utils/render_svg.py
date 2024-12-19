from pathlib import Path
from PIL import Image
from io import BytesIO


def render_svg_from_file(svg_file: Path, size: tuple = None) -> Image:
    if not svg_file.exists():
        raise FileNotFoundError(f"File not found: {svg_file}")
    with open(svg_file, "r") as file:
        svg_data = file.read()
    return render_svg(svg_data, size)


def render_svg(svg_data: str, size: tuple = None) -> Image:
    try:
        import cairosvg
    except  ImportError:
        raise ImportError("cairosvg is not installed. Please install it using 'pip install cairosvg'")
    png_data = cairosvg.svg2png(bytestring=svg_data, output_width=size[0] if size else None, output_height=size[1] if size else None)
    return Image.open(BytesIO(png_data))


def render(svg_source, size: tuple = None):
    if isinstance(svg_source, Path):
        return render_svg_from_file(svg_source)
    elif isinstance(svg_source, str):
        if is_svg_file(Path(svg_source)):
            return render_svg_from_file(Path(svg_source), size)
        elif is_svg_data(svg_source):
            return render_svg(svg_source, size)
        else:
            raise ValueError('Not a valid SVG file or data')
    else:
        raise ValueError('Not a valid SVG source')


def is_svg_file(file_path: Path) -> bool:
    return file_path.suffix.lower() == '.svg' and file_path.exists() and file_path.is_file()


def is_svg_data(svg_data: str) -> bool:
    return svg_data.strip().startswith('<svg') and svg_data.strip().endswith('</svg>')