import os

from cea.interfaces.dashboard.settings import get_settings


class InvalidPathError(Exception):
    """Raised when a path is invalid (e.g. outside or project root folder)"""


def secure_path(path: str) -> str:
    """
    Simple sanitation of path
    """
    project_root = get_settings().project_root
    real_path = os.path.realpath(path)
    rel_path = os.path.relpath(real_path, project_root)

    if ".." in rel_path:
        raise InvalidPathError("Path is outside of project root")

    return real_path
