import os

from cea.interfaces.dashboard.settings import get_settings


class InvalidPathError(Exception):
    """Raised when a path is invalid (e.g. outside or project root folder)"""


def secure_path(path: str) -> str:
    """
    Simple sanitation of path
    """
    real_path = os.path.realpath(path)

    if not get_settings().allow_path_transversal():
        project_root = os.path.realpath(get_settings().project_root)

        prefix = os.path.commonpath((project_root, real_path))
        if project_root != prefix:
            raise InvalidPathError("Path is outside of project root")

    return real_path
