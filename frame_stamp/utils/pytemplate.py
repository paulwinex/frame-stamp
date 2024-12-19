import importlib.util
from pathlib import Path


def import_py_template(path, **kwargs):
    module = import_module_from_path('frame_stamp_template_file', path)
    if not hasattr(module, 'get_template'):
        raise ImportError(f"Module {path} has not contains function get_template")
    return module.get_template(**kwargs)


def import_module_from_path(module_name: str, file_path: str):
    file_path = Path(file_path).resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"Файл по пути {file_path} не существует.")

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        raise ImportError(f"Не удалось создать спецификацию для модуля {module_name} из файла {file_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module