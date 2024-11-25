import abc
import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from functools import wraps

from typing import Tuple, Callable, Collection, NamedTuple

from cea import MissingInputDataException

locator_func = Callable[..., str]
locator_func_args = Collection[str]


class Category(NamedTuple):
    name: str
    label: str


class MapLayer(abc.ABC):
    category: Category
    name: str
    label: str
    description: str

    def __init__(self, project: str, parameters: dict):
        self.project = project
        self.parameters = parameters

        self._validate_parameters()
        self.check_for_missing_input_files()

    @classmethod
    def describe(cls) -> dict:
        return {
            "category": cls.category._asdict(),
            "name": cls.name,
            "label": cls.label,
            "description": cls.description,
            "parameters": cls.expected_parameters()
        }

    @classmethod
    @abc.abstractmethod
    def expected_parameters(self) -> dict:
        """Returns a dictionary of parameters that are expected to be set for this layer"""

    @property
    @abc.abstractmethod
    def input_file_locators(self) -> Collection[Tuple[locator_func, locator_func_args]]:
        """Returns a collection of callables that are used to generate the input file paths used for this layer"""

    def _validate_parameters(self) -> None:
        """Validates the parameters"""

    @property
    def input_files(self) -> Collection[str]:
        for locator_descriptor in self.input_file_locators:
            locator_callable = locator_descriptor
            if len(locator_descriptor) > 1:
                func, args = locator_descriptor

                def _callable():
                    return func(*args)

                locator_callable = _callable

            yield locator_callable()

    def check_for_missing_input_files(self) -> None:
        """Checks if all input files are present"""
        missing_input_files = set()

        def add_missing_input_file(path):
            if not os.path.isfile(path):
                missing_input_files.add(path)

        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(add_missing_input_file, self.input_files)

        if missing_input_files:
            raise MissingInputDataException(f"Following input files are missing: {missing_input_files}")

    @abc.abstractmethod
    def generate_output(self) -> dict:
        """Generates the output for this layer"""


# TODO: Add support for caching the output if the input files are not stored locally
def cache_output(method):
    """
    Decorator to cache the output of a method based on file modification times
    and an additional 'parameters' dictionary, storing the result in a JSON file
    within the object's 'project' directory.
    """
    @wraps(method)
    def wrapper(self: MapLayer, *args, **kwargs):
        # Ensure the object has the required attributes
        if not hasattr(self, 'input_files'):
            raise AttributeError("Object must have an 'input_files' property returning a list of file paths.")
        if not hasattr(self, 'parameters') or not isinstance(self.parameters, dict):
            raise AttributeError("Object must have a 'parameters' attribute of type dict.")
        if not hasattr(self, 'project') or not isinstance(self.project, str):
            raise AttributeError("Object must have a 'project' attribute specifying the cache directory.")

        # Function to check file existence and modification time
        def get_file_state(file_path):
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Input file {file_path} does not exist.")
            return file_path, os.path.getmtime(file_path)

        # Use ThreadPoolExecutor for parallel file state retrieval
        with ThreadPoolExecutor() as executor:
            file_states = list(executor.map(get_file_state, self.input_files))

        # Combine file states and parameters into a single cache key
        cache_key_data = {
            "files": file_states,
            "parameters": self.parameters
        }
        cache_key = hashlib.sha256(json.dumps(cache_key_data, sort_keys=True).encode()).hexdigest()

        # Define the cache file path
        cache_directory = os.path.join(self.project, ".cache", "map_layers", self.name)
        os.makedirs(cache_directory, exist_ok=True)
        cache_file = os.path.join(cache_directory, f"{cache_key}.json")

        # Check if the cache file exists
        if os.path.exists(cache_file):
            # Load the cached result
            with open(cache_file, 'r') as f:
                return json.load(f)

        # Compute the result and store it in the cache file
        result = method(self, *args, **kwargs)
        if not isinstance(result, dict):
            raise ValueError("The method must return a dictionary to be stored as JSON.")

        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=4)

        return result

    return wrapper
