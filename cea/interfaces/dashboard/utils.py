import importlib
import inspect
import os
from typing import List, Any, Type, Union

from cea.interfaces.dashboard.settings import get_settings


class OutsideProjectRootError(Exception):
    """Raised when a path is outside or project root folder"""
    def __init__(self, path):
        super().__init__(f"Path `{path}` is not a valid path.")
        self.path = path

def secure_path(path: Union[str, os.PathLike]) -> str:
    """
    Simple sanitation of path
    """
    real_path = os.path.realpath(path)

    # TODO: Remove dependency on settings
    if not get_settings().allow_path_transversal():
        settings_project_root = get_settings().project_root
        if settings_project_root is None:
            raise ValueError("Project root not set. Unable to determine project root.")
        
        project_root = os.path.realpath(settings_project_root)
        prefix = os.path.commonpath((project_root, real_path))
        if project_root != prefix:
            raise OutsideProjectRootError(path)

    return real_path


def find_subclasses_in_path(parent_class: Type, path: str) -> List[Any]:
    classes_found = []

    # Walk through all files in the directory and subdirectories
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                module_path = os.path.join(root, file)
                module_name = os.path.splitext(file)[0]

                # Load the module from file path
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Inspect all members of the module to find classes
                for name, obj in inspect.getmembers(module):
                    # Check if the member is a class and is a subclass of the parent class
                    if inspect.isclass(obj) and issubclass(obj, parent_class) and obj is not parent_class:
                        classes_found.append(obj)

    return classes_found