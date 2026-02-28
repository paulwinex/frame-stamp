"""
A JSON wrapper with C++ support and Python comments.
For comments, use double forward slashes (`//`)

Example

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


def load(fp, *args, **kwargs) -> str:
    """
    Uploading a JSON file with comments. All comments are removed during upload.
    """
    try:
        return __clear_comments(fp.read(), **kwargs)
    except Exception as e:
        raise Exception("{} {}".format(e, "File: {}".format(fp.name) if hasattr(fp, 'name') else ''))


def loads(text: str, *args, **kwargs) -> str:
    """
    Loading JSON from a string with comments stripped
    """
    return __clear_comments(text, **kwargs)


def dumps(obj: object, comment: str = None, **kwargs) -> str:
    """
    Write JSON to a string with the option to add a comment at the very beginning
    """
    if not comment:
        return _dumps(obj, **kwargs)
    else:
        text = _dumps(obj, **kwargs)
        text = '//{}\n{}'.format(comment, text)
        return text


def dump(obj: object, fp, comment: str = None, **kwargs) -> int:
    """
    Write JSON to a file with the option to add a comment at the very beginning
    """
    if not comment:
        return _dump(obj, fp, **kwargs)
    else:
        text = dumps(obj, comment=comment, **kwargs)
        return fp.write(text)


def __clear_comments(text: str, **kwargs) -> str:
    """
    Clearing comments from a line
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
