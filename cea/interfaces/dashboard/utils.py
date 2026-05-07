import importlib
import inspect
import os
from typing import List, Any, Optional, Type, Union

from fastapi import HTTPException, status

from cea.interfaces.dashboard.settings import get_settings
from cea.utilities import validate_path_within_root


class OutsideProjectRootError(Exception):
    """Raised when a path is outside or project root folder"""
    def __init__(self, path):
        super().__init__(f"Path `{path}` is not a valid path.")
        self.path = path

def secure_path(path: Union[str, os.PathLike], root: Union[str, os.PathLike, None] = None) -> str:
    """
    Validates and sanitizes a file path to prevent directory traversal attacks.

    Resolves the path to its canonical form (following symlinks) and ensures it
    stays within the project root directory.

    Args:
        path: Path to validate (can be relative or absolute)

    Returns:
        Canonical absolute path as string

    Raises:
        ValueError: If project root is not set when path validation is enabled
        OutsideProjectRootError: If resolved path is outside the project root
    """
    # Resolve to canonical absolute path (follows symlinks, normalizes . and ..)
    real_path = os.path.realpath(path)

    # TODO: Remove dependency on settings
    if not get_settings().allow_path_transversal():
        if root is not None:
            project_root = os.path.realpath(root)
        else:
            settings_project_root = get_settings().project_root
            if settings_project_root is None:
                raise ValueError("Project root not set. Unable to determine project root.")
            project_root = os.path.realpath(settings_project_root)

        try:
            real_path = validate_path_within_root(real_path, project_root)
        except ValueError:
            raise OutsideProjectRootError(path)

    return real_path


def resolve_scenario_path(
    project_root: Optional[str],
    project: str,
    scenario: str,
) -> str:
    """Resolve and validate a scenario path from project + scenario name.

    Shared by endpoints (Reports, Inputs) that accept an explicit
    `project` + `scenario` pair so they can operate on a scenario
    other than the dashboard's currently active one.
    """
    project_path = project
    if project_root is not None and not project_path.startswith(project_root):
        project_path = os.path.join(project_root, project_path)

    project_path = secure_path(project_path)
    scenario_path = os.path.join(project_path, scenario)

    if not os.path.isdir(scenario_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Scenario not found: {scenario}",
        )
    return scenario_path


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