import os
from functools import wraps
import subprocess
from pydoc import locate
import math


USE_CACHE = not bool(os.getenv('NO_CACHE'))


def cached_result(func):
    """
    Кеширование значения для шейп
    """
    @wraps(func)
    def wrapped(*args, **kwargs):
        if USE_CACHE:
            inst = args[0]
            try:
                result = getattr(inst, '__cache__')[func.__name__]
            except AttributeError:  # no cache
                result = func(*args, **kwargs)
                inst.__cache__ = {func.__name__: result}
            except KeyError:    # not saved yet
                result = func(*args, **kwargs)
                inst.__cache__[func.__name__] = result
        else:
            result = func(*args, **kwargs)
        return result
    return wrapped


def load_from_dotted(name):
    """
    Импорт модуля по имени

    Parameters
    ----------
    name: str

    Returns
    -------
    object
    """
    mod = locate(name)
    if mod:
        return mod
    try:
        return __import__(name)
    except ImportError:
        return


def open_file_location(path):
    if not os.path.exists(path):
        raise IOError('Path not exists: {}'.format(path))
    if os.name == 'nt':
        os.startfile(path)
    elif os.name == 'posix':
        subprocess.call(('xdg-open', path))
    else:   # mac os
        subprocess.call(('open', path))


def rotate_point(point: list, angle, origin: list = None,  precision=3):
    """
    Rotate a point counterclockwise by a given angle around a given origin.
    The angle should be given in degrees.

    """
    origin = origin or (0, 0)
    ox, oy = origin
    px, py = point
    rad = math.radians(angle)
    qx = ox + math.cos(rad) * (px - ox) - math.sin(rad) * (py - oy)
    qy = oy + math.sin(rad) * (px - ox) + math.cos(rad) * (py - oy)
    return round(qx, precision), round(qy, precision)
