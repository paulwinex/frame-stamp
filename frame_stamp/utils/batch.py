from pathlib import Path

from frame_stamp.stamp import FrameStamp
import copy


def batch_with_sequences(source_images: list[str],
                         template: dict,
                         variables: dict,
                         output_file_name: str,
                         output_path: str):
    """
    Use list values as frame values
    Example:
        {
            "variables": {
                "name": "Example",
                "frames": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            }
        }
    """
    for i, image in enumerate(source_images):
        _variables = {}
        for key, value in variables.items():
            if isinstance(value, list):
                _variables[key] = value[i]
            else:
                _variables[key] = value
        stamp = FrameStamp(image, template, _variables)
        stamp.render(save_path=Path(output_path, f'{output_file_name}'+str(i).zfill(3)).with_suffix('.png'))

