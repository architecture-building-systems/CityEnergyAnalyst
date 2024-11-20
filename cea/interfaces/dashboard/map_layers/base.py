import abc
import os
from concurrent.futures import ThreadPoolExecutor

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
    def input_files(self) -> Collection[Tuple[locator_func, locator_func_args]]:
        """Returns a collection of callables that are used to generate the input file paths used for this layer"""

    def _validate_parameters(self) -> None:
        """Validates the parameters"""

    def check_for_missing_input_files(self) -> None:
        """Checks if all input files are present"""
        missing_input_files = set()

        def generate_file_list():
            for locator_descriptor in self.input_files:
                locator_callable = locator_descriptor
                if len(locator_descriptor) > 1:
                    func, args = locator_descriptor

                    def _callable():
                        return func(*args)

                    locator_callable = _callable

                yield locator_callable()

        def add_missing_input_file(path):
            if not os.path.isfile(path):
                missing_input_files.add(path)

        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(add_missing_input_file, generate_file_list())

        if missing_input_files:
            raise MissingInputDataException(f"Following input files are missing: {missing_input_files}")

    @abc.abstractmethod
    def generate_output(self) -> dict:
        """Generates the output for this layer"""
