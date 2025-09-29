import abc
import functools
import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import wraps

from typing import NamedTuple, List, Optional, Dict, Any

from cea import MissingInputDataException
from cea.config import Configuration, DEFAULT_CONFIG
from cea.inputlocator import InputLocator
from cea.interfaces.dashboard.lib.logs import getCEAServerLogger


logger = getCEAServerLogger("cea-server-map-layers")


# locator_func = Callable[..., str]
# locator_func_args = Collection[str]

@dataclass()
class ColourGradient:
    colour_array: List[str]
    points: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "colour_array": self.colour_array,
            "points": self.points
        }

@dataclass()
class FileRequirement:
    """
    Defines the requirements for input files based on selected parameters
    """
    description: str
    file_locator: str
    depends_on: Optional[List[str]] = None
    """A list of parameter names that this file requirement depends on."""

    def get_required_files(self, layer: "MapLayer", current_params: Dict[str, Any]) -> List[str]:
        """
        Find files matching the requirements based on current parameters
        """
        if self.depends_on is not None:
            # Check if the current parameters meet the requirements
            missing = [value for value in self.depends_on if value not in current_params]
            if missing:
                logger.error(f"Missing required parameters for file requirement [{self.file_locator}]: {missing}")
                raise ValueError(f"Missing required parameters: [{missing}]")

        # Parse string locator
        class_name, method_name = self.file_locator.rsplit(":", 1)
        if class_name == "locator":
            func = getattr(layer.locator, method_name)
        elif class_name == "layer":
            func = getattr(layer, method_name)
            func = functools.partial(func, current_params)
        else:
            raise ValueError(f"Invalid class name: {class_name}")

        files = func()

        return files

    def to_dict(self) -> dict:
        """Convert FileRequirement to a dictionary"""
        return {
            "description": self.description,
            "depends_on": self.depends_on
        }


# TODO: Create subclasses for each type of parameter
@dataclass()
class ParameterDefinition:
    """
    Defines the structure and constraints of a parameter
    """
    label: str
    type: str
    description: Optional[str] = None
    default: Any = None
    options_generator: Optional[str] = None
    depends_on: Optional[List[str]] = None
    selector: Optional[str] = None
    range: Optional[List[float]] = None
    filter: Optional[str] = None

    def generate_choices(self, layer: "MapLayer", current_params: dict) -> dict:
        """Generate value based on current parameters"""
        if self.options_generator is None:
            raise ValueError("Parameter does not support choices")

        if self.depends_on is None:
            func = getattr(layer, self.options_generator)
            return func()

        if not all(k in current_params for k in self.depends_on):
            raise ValueError("Missing required parameters for generating choices")

        func = getattr(layer, self.options_generator)
        func = functools.partial(func, current_params)

        return func()

    def generate_range(self, layer: "MapLayer", current_params: dict) -> List[float]:
        """Generate dynamic range for slider selector based on current parameters"""
        if self.options_generator is None:
            raise ValueError("Parameter does not support dynamic range")

        if self.depends_on is None:
            func = getattr(layer, self.options_generator)
            return func()
        
        missing = [value for value in self.depends_on if value not in current_params]
        if missing:
            logger.error(f"Missing required parameters for range generation [{self.label}]: {missing}")
            raise ValueError(f"Missing required parameters: [{missing}]")

        func = getattr(layer, self.options_generator)
        func = functools.partial(func, current_params)
        range_values = func()

        # Ensure the result is a 2-item list [min, max]
        if not isinstance(range_values, list) or len(range_values) != 2:
            raise ValueError("Range generator must return a 2-item list [min, max]")

        return range_values

    def to_dict(self) -> dict:
        """Convert ParameterDefinition to a dictionary"""
        result = {
            "label": self.label,
            "type": self.type,
            "default": self.default,
            "depends_on": self.depends_on,
            "description": self.description,
            "selector": self.selector,
            "range": self.range,
            "filter": self.filter
        }
        
        return result


class Category(NamedTuple):
    name: str
    label: str


class MapLayer(abc.ABC):
    category: Category
    name: str
    label: str
    description: str

    def __init__(self, project: str, scenario_name: str):
        self.project = project
        self.scenario_name = scenario_name

        self.config = Configuration(DEFAULT_CONFIG)
        self.config.project = self.project
        self.config.scenario_name = self.scenario_name

        self.locator = InputLocator(self.config.scenario)

    @classmethod
    def describe(cls) -> dict:
        return {
            "category": cls.category._asdict(),
            "name": cls.name,
            "label": cls.label,
            "description": cls.description,
            "parameters": {k: v.to_dict() for k, v in cls.expected_parameters().items()}
        }

    @classmethod
    @abc.abstractmethod
    def expected_parameters(cls) -> Dict[str, ParameterDefinition]:
        """Returns a dictionary defining the expected parameters for this layer"""

    @classmethod
    @abc.abstractmethod
    def file_requirements(cls) -> List[FileRequirement]:
        """Define file requirements for the layer"""

    @abc.abstractmethod
    def generate_data(self, parameters: dict) -> dict:
        """Generates the data for this layer"""

    def validate_parameters(self, parameters: dict) -> None:
        """Validates the parameters for this layer"""
        for name, parameter in self.expected_parameters().items():
            if parameter.depends_on is not None and name in parameters:
                if not all(value in parameters for value in parameter.depends_on):
                    raise ValueError(f"Parameters {parameter.depends_on} are required for {name}")

    def get_parameter_choices(self, parameter_name: str, parameters: dict) -> dict:
        """Returns the choices for the parameters for this layer"""
        parameter_def = self.expected_parameters().get(parameter_name)
        if parameter_def is None:
            raise ValueError(f"Parameter {parameter_name} not found")
        choices = parameter_def.generate_choices(self, parameters)
        return choices

    def get_parameter_range(self, parameter_name: str, parameters: dict) -> List[float]:
        """Returns the dynamic range for slider parameters"""
        parameter_def = self.expected_parameters().get(parameter_name)
        if parameter_def is None:
            raise ValueError(f"Parameter {parameter_name} not found")
        range_values = parameter_def.generate_range(self, parameters)
        return range_values

    def get_required_files(self, parameters) -> List[str]:
        """Returns the list of required files for this layer"""
        required_files = set()
        for file_requirement in self.file_requirements():
            files = file_requirement.get_required_files(self, parameters)

            if isinstance(files, list):
                required_files.update(files)
            else:
                required_files.add(files)

        return list(required_files)

    def check_for_missing_input_files(self, parameters: dict) -> None:
        """Checks if all input files are present"""
        missing_input_files = set()
        required_files = self.get_required_files(parameters)

        def add_missing_input_file(path):
            if not os.path.isfile(path):
                missing_input_files.add(path)

        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(add_missing_input_file, required_files)

        if missing_input_files:
            raise MissingInputDataException(f"Following input files are missing: {missing_input_files}")

    def generate_output(self, parameters) -> dict:
        """Generates the output for this layer"""
        # Validate parameters
        self.validate_parameters(parameters)

        # Check for missing input files
        self.check_for_missing_input_files(parameters)

        # Generate the data
        data = self.generate_data(parameters)

        return data


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
        if not hasattr(self, 'get_required_files'):
            raise AttributeError("Object must have 'get_required_files' method returning a list of file paths.")
        if not hasattr(self, 'project') or not isinstance(self.project, str):
            raise AttributeError("Object must have a 'project' attribute specifying the cache directory.")

        parameters = args[0]
        if not parameters:
            raise ValueError("Missing 'parameters' argument")

        # Function to check file existence and modification time
        def get_file_state(file_path):
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Input file {file_path} does not exist.")
            return file_path, os.path.getmtime(file_path)

        # Use ThreadPoolExecutor for parallel file state retrieval
        with ThreadPoolExecutor() as executor:
            file_states = list(executor.map(get_file_state, self.get_required_files(parameters)))

        # Combine file states and parameters into a single cache key
        cache_key_data = {
            "files": file_states,
            "parameters": parameters
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
