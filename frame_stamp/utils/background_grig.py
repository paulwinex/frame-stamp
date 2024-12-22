from PIL import Image, ImageDraw, ImageFont

from frame_stamp.utils.rect import Rect


def create_grid_image(save_path: str, size: list,
                      background_color="#909090", line10color="#717171", line100color="#424242",
                      add_labels=True, label_color="#000000",
                      safe_frame=True, center_cross=True):
    width, height = size
    img = Image.new('RGB', (width, height), color=background_color)
    draw = ImageDraw.Draw(img)

    font = ImageFont.load_default()

    # grid
    lines10 = []
    linex100 = []
    for x in range(0, width, 10):
        coords = [(x, 0), (x, height)]
        if x % 100 != 0:
            lines10.append(coords)
        else:
            linex100.append(coords)
    for y in range(0, height, 10):
        coords = [(0, y), (width, y)]
        if y % 100 != 0:
            lines10.append(coords)
        else:
            linex100.append(coords)
    for line in lines10:
        draw.line(line, fill=line10color, width=1)
    for line in linex100:
        draw.line(line, fill=line100color, width=1)
    # labels
    if add_labels:
        for x in range(0, width, 100):
            for y in range(0, height, 100):
                label = f"({x}, {y})"
                bbox = draw.textbbox((0, 0), label, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                if x + text_width < width and y + text_height < height:
                    text_position = (x + 2, y + 2)
                elif x + text_width >= width and y + text_height < height:
                    text_position = (x - text_width - 2, y + 2)
                elif x + text_width < width and y + text_height >= height:
                    text_position = (x + 2, y - text_height - 2)
                else:
                    text_position = (x - text_width - 2, y - text_height - 2)

                draw.text(text_position, label, font=font, fill=label_color)
    # cross
    if center_cross:
        draw.line(((0, 0), (width, height)), fill=line10color, width=1)
        draw.line(( (0, height), (width, 0)), fill=line10color, width=1)
    # safe frame
    if safe_frame:
        rect = Rect(0, 0, width, height)
        h_adjust = rect.width * 0.1
        v_adjust = rect.height * 0.1
        rect = rect.adjusted(h_adjust, v_adjust, h_adjust, v_adjust)
        draw.rectangle(rect.corners(), outline=line100color, width=1)

    img.save(save_path)
    return save_path