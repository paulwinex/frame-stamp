import os
from functools import wraps
import subprocess
from pydoc import locate

USE_CACHE = not bool(os.getenv('NO_CACHE'))


def cached_result(func):
    """
    Кеширование значения для шейп
    """
    @wraps(func)
    def wrapped(*args, **kwargs):
        if USE_CACHE:
            inst = args[0]
            cache_key = f'{func.__qualname__}'
            try:
                result = getattr(inst, '__cache__')[cache_key]
            except AttributeError:  # no cache
                result = func(*args, **kwargs)
                if result is not None:
                    inst.__cache__ = {cache_key: result}
            except KeyError:    # not saved yet
                result = func(*args, **kwargs)
                if result is not None:
                    inst.__cache__[cache_key] = result
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


