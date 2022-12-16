# coding=utf-8
"""
Обёртка для Json c поддержкой C++ и python комментариев.
Для коментариев используйте двойной прямой слеш (`//`)

Пример

.. code-block:: json

   {
       // key 1 for action 1
       "KEY1": "value",
       // key 2 for action 2
       "KEY1": 123
   }

"""
import re
from json import loads as _loads, dumps as _dumps, dump as _dump


def load(fp, *args, **kwargs):
    """
    Загрузка JSON файла с комментациями. Во время загрузки все комментарии удаляются

    Parameters
    ----------
    fp: file
    args
    kwargs

    Returns
    -------
    Any
    """
    try:
        return __clear_comments(fp.read(), **kwargs)
    except Exception as e:
        raise Exception("{} {}".format(e, "File: {}".format(fp.name) if hasattr(fp, 'name') else ''))


def loads(text, *args, **kwargs):
    """
    Загрзка JSON из строки с очисткой коментариев

    Parameters
    ----------
    text: str
    args
    kwargs

    Returns
    -------
    object
    """
    return __clear_comments(text, **kwargs)


def dumps(obj, comment=None, **kwargs):
    """
    Запись JSON в строку с возможностью добавить комментарий в самом начале

    Parameters
    ----------
    obj: object
    comment: str
    kwargs

    Returns
    -------
    str
    """
    if not comment:
        return _dumps(obj, **kwargs)
    else:
        text = _dumps(obj, **kwargs)
        text = '//{}\n{}'.format(comment, text)
        return text


def dump(obj, fp, comment=None, **kwargs):
    """
    Запись JSON в файл с возможностью добавить комментарий в самом начале

    Parameters
    ----------
    obj: object
    comment: str
    kwargs

    Returns
    -------
    int
    """
    if not comment:
        return _dump(obj, fp, **kwargs)
    else:
        text = dumps(obj, comment=comment, **kwargs)
        return fp.write(text)


def __clear_comments(text, **kwargs):
    """
    Очистка комментариев из строки

    Returns
    -------
    str
    """

    regex = r'\s*(/{2}).*$'
    regex_inline = r'(:?(?:\s)*([A-Za-z\d.{}]*)|((?<=\").*\"),?)(?:\s)*(((/{2}).*)|)$'
    lines = text.split('\n')
    for index, line in enumerate(lines):
        if re.search(regex, line):
            if re.search(r'^' + regex, line, re.IGNORECASE):
                lines[index] = ""
            elif re.search(regex_inline, line):
                lines[index] = re.sub(regex_inline, r'\1', line)
    multiline = re.compile(r"/\*.*?\*/", re.DOTALL)
    cleaned_text = re.sub(multiline, "", '\n'.join(lines))
    return _loads(cleaned_text, **kwargs)
