import math
from PIL import Image, ImageDraw


def linear_gradient(size: tuple[int, int], point1: tuple[int, int, int], point2: tuple[int, int, int],
                    color1: tuple[int, int, int, int], color2: tuple[int, int, int, int], **kwargs):
    assert len(size) == 2, "Size must be a tuple of (width, height)"
    assert len(point1) == 2, "Point1 must be a tuple of (x, y)"
    assert len(point2) == 2, "Point2 must be a tuple of (x, y)"
    assert len(color1) == 4, "Color1 must be a tuple of (r, g, b, a)"
    assert len(color2) == 4, "Color2 must be a tuple of (r, g, b, a)"

    img = Image.new('RGBA', size)
    draw = ImageDraw.Draw(img)
    width, height = size
    x1, y1 = max(0, min(point1[0], width - 1)), max(0, min(point1[1], height - 1))
    x2, y2 = max(0, min(point2[0], width - 1)), max(0, min(point2[1], height - 1))
    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx * dx + dy * dy)
    if length == 0:
        return img
    for y in range(height):
        for x in range(width):
            t = ((x - x1) * dx + (y - y1) * dy) / (length * length)
            t = max(0, min(t, 1))
            r = int(color1[0] + (color2[0] - color1[0]) * t)
            g = int(color1[1] + (color2[1] - color1[1]) * t)
            b = int(color1[2] + (color2[2] - color1[2]) * t)
            a = int(color1[3] + (color2[3] - color1[3]) * t)
            draw.point((x, y), (r, g, b, a))
    return img


def radial_gradient(size: tuple[int, int], center: tuple[int, int], radius: int,
                    color1: tuple[int, int, int, int], color2: tuple[int, int, int, int], **kwargs):
    assert len(size) == 2, "Size must be a tuple of (width, height)"
    assert len(center) == 2, "Center must be a tuple of (x, y)"
    assert len(color1) == 4, "Color1 must be a tuple of (r, g, b, a)"
    assert len(color2) == 4, "Color2 must be a tuple of (r, g, b, a)"
    assert radius > 0, "Radius must be greater than 0"

    img = Image.new('RGBA', size)
    draw = ImageDraw.Draw(img)
    width, height = size
    cx, cy = center
    for y in range(height):
        for x in range(width):
            dist = math.hypot(x - cx, y - cy)
            if dist >= radius:
                r, g, b, a = color2
            else:
                norm_dist = dist / radius
                r = int(color1[0] + (color2[0] - color1[0]) * norm_dist)
                g = int(color1[1] + (color2[1] - color1[1]) * norm_dist)
                b = int(color1[2] + (color2[2] - color1[2]) * norm_dist)
                a = int(color1[3] + (color2[3] - color1[3]) * norm_dist)
            final_alpha = int(a * 255 / 255)
            draw.point((x, y), (r, g, b, final_alpha))
    return img


def get_gradient_renderer(gradient_type):
    if gradient_type == 'linear':
        return linear_gradient
    elif gradient_type == 'radial':
        return radial_gradient
    else:
        raise ValueError(f"Unknown gradient type: {gradient_type}")


def mix_alpha_channels(img1, img2):
    """
    Mix alpha img1 > img2
    img2 will be changed
    """
    if img1.mode == 'L':
        alpha = img1
    elif img1.mode == 'RGB':
        alpha = img1.convert('RGBA').split()[3]
    elif img1.mode == 'RGBA':
        alpha = img1.split()[3]
    else:
        raise ValueError('Image mode must be "L" or "RGB" or "RGBA"')

    if img2.mode != 'RGBA':
        img2 = img2.convert('RGBA')

    width, height = img2.size
    alpha_data = alpha.load()
    img2_data = img2.load()
    for y in range(height):
        for x in range(width):
            pixel1 = alpha_data[x, y]
            pixel2 = img2_data[x, y]
            alpha1 = pixel1 / 255
            alpha2 = pixel2[3] / 255
            new_alpha = int(alpha1 * alpha2 * 255)
            img2_data[x, y] = (pixel2[0], pixel2[1], pixel2[2], new_alpha)
