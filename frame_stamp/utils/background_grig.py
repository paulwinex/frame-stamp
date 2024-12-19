from PIL import Image, ImageDraw, ImageFont


def create_grid_image(save_path: str, size: list, background_color="#909090", line10color="#717171", line100color="#424242",
                      add_labels=True):
    width, height = size
    img = Image.new('RGB', (width, height), color=background_color)
    draw = ImageDraw.Draw(img)

    font = ImageFont.load_default()

    for x in range(0, width, 10):
        line_color = line10color if x % 100 != 0 else line100color
        draw.line([(x, 0), (x, height)], fill=line_color, width=1)

    for y in range(0, height, 10):
        line_color = line10color if y % 100 != 0 else line100color
        draw.line([(0, y), (width, y)], fill=line_color, width=1)

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

                draw.text(text_position, label, font=font, fill="#000000")

    img.save(save_path)
    return save_path