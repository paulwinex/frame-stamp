import multiprocessing
from pathlib import Path
import logging
from .stamp import FrameStamp
from PIL import Image
import itertools
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor


def process_sequence(src_dir: str, output_dir: str, template: dict, context: dict, file_pattern: str = '*.*',
                     multithread=True, context_callback=None, **kwargs):
    src_dir = Path(src_dir)
    if not src_dir.exists():
        raise IOError(f'Source path not exists {src_dir}')
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    files = sorted(src_dir.glob(file_pattern))
    if kwargs.get('limit'):
        files = files[:kwargs['limit']]
    if multithread:
        run_multiprocess(files, template, output_dir, context, context_callback=context_callback, **kwargs)


def _executor_helper(kwargs):
    try:
        render_single_frame(**kwargs)
    except Exception as e:
        logging.exception('Render error')


def run_multiprocess(files, template, output_path, context, **kwargs):
    # get cp count
    cpu_count = context.get('render_cpu_count') or multiprocessing.cpu_count()
    logging.info(f'Use Multiprocess render ({cpu_count} cpu)')
    # start pool
    callback = kwargs.get('context_callback')
    with ProcessPoolExecutor() as executor:
        executor.map(_executor_helper, (dict(
            image_path=file,
            save_path=Path(output_path, file.name),
            template=template,
            context={**context, 'frame': i, 'file': file, 'total_frames': len(files),
                     **(callback(i, file, len(files), **kwargs) if callback else {})}
        ) for i, file in enumerate(files)))


def render_single_frame(image_path: str, save_path: str, template: dict, context: dict):
    image_path = Path(image_path)
    # logging.info(f'Process file {image_path.name}')
    save_path = Path(save_path)
    img = Image.open(str(image_path))
    renderer = FrameStamp(img, template, context)
    img = renderer.render()
    img.save(save_path.as_posix(), save_path.suffix.strip('.').upper())
    return save_path
