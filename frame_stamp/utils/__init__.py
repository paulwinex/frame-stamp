import os
from functools import wraps

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
