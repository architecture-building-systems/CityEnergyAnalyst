#!/usr/bin/env python
"""
Utility to generate type stubs for cea.config based on default.config

This script automatically generates the config.pyi type stub file by:
1. Parsing default.config to extract all sections and parameters
2. Inspecting the cea.config module for classes, methods, and constants
3. Inferring types from Parameter class decode methods
4. Generating typed section classes with proper type hints

Run this script manually when default.config changes:
    python -m cea.utilities.config_type_generator

Or it will run automatically via GitHub Actions when:
- cea/config.py changes
- cea/default.config changes
- cea/utilities/config_type_generator.py changes

See .github/workflows/update-config-stubs.yml for the automation workflow.
"""

import configparser
import os
import inspect
import importlib
from typing import List, Optional


def _ann_to_stub_str(ann: object) -> str:
    """Convert an annotation object to a stub-friendly string"""
    s = getattr(ann, "__name__", None) or str(ann)

    # Strip typing.ForwardRef('X') -> X
    if "ForwardRef(" in s:
        import re
        match = re.search(r"ForwardRef\(['\"]([^'\"]+)['\"]\)", s)
        if match:
            # Return the name without quotes (from __future__ import annotations handles it)
            return match.group(1)

    # typing module strings -> prefer bare names when imported (e.g., List[str])
    s = s.replace("typing.", "")

    return s


def infer_type_from_decode_method(param_class_name: str) -> str:
    """Analyze the decode method of a parameter class to infer its return type"""

    # Import the config module to analyze the actual classes
    config_mod = importlib.import_module("cea.config")
    Parameter = config_mod.Parameter

    # Get all Parameter subclasses
    param_classes = {}
    for name in dir(config_mod):
        obj = getattr(config_mod, name)
        if inspect.isclass(obj) and issubclass(obj, Parameter) and obj != Parameter:
            param_classes[name] = obj

    if param_class_name not in param_classes:
        return "Any"

    cls = param_classes[param_class_name]

    # Get the decode method (may be inherited)
    decode_method = getattr(cls, 'decode', None)
    if decode_method is None:
        return "str"  # No decode method found

    # First, try to get the return type annotation from the decode method
    try:
        sig = inspect.signature(decode_method)
        if sig.return_annotation != inspect.Parameter.empty:
            return _ann_to_stub_str(sig.return_annotation)
    except Exception:
        pass

    # Check if class has a custom decode method (not inherited from base Parameter)
    # If it only has the base Parameter.decode, return str
    if decode_method == Parameter.decode:
        return "str"  # Default Parameter.decode returns string

    # Fall back to analyzing the decode method source with heuristics
    try:
        source = inspect.getsource(decode_method)

        # Simple heuristics based on common patterns
        if "return int(" in source or "return int(value)" in source:
            return "int"
        elif "return float(" in source or "return float(value)" in source:
            return "float"
        elif "return self._boolean_states" in source or "return bool(" in source:
            return "bool"
        elif "parse_string_coordinate_list" in source or "coordinate" in source.lower():
            return "List[Tuple[float, float]]"
        elif (
            "parse_string_to_list" in source
            or "return [" in source
            or "List[" in source
        ):
            return "List[str]"
        elif "return str(" in source or "return value" in source:
            return "str"
        elif "return None" in source and "nullable" in source:
            # This parameter can return None, use Optional
            if "return int(" in source:
                return "Optional[int]"
            elif "return float(" in source:
                return "Optional[float]"
            else:
                return "Optional[str]"
        elif "json.loads" in source:
            # JSON can be anything and can return None
            return "Optional[Any]" if "return None" in source else "Any"
        elif "datetime" in source:
            return "datetime.datetime"
        else:
            return "str"  # Default fallback

    except Exception:
        return "str"  # Fallback if source analysis fails


def infer_type_from_param_class_name(
    param_class_name: str,
    section_name: Optional[str] = None,
    param_name: Optional[str] = None,
    config_parser: Optional[configparser.ConfigParser] = None
) -> str:
    """Special handling for known parameter types that need different inference

    Args:
        param_class_name: The Parameter class name (e.g., "IntegerParameter")
        section_name: The config section name (optional, for checking nullable)
        param_name: The parameter name (optional, for checking nullable)
        config_parser: The config parser (optional, for checking nullable)
    """
    # Special case for PluginListParameter - returns plugin instances, not strings
    if param_class_name == "PluginListParameter":
        return "List[Any]"

    # Get base type from decode method inference
    base_type = infer_type_from_decode_method(param_class_name)

    # Strip existing | None from the base type if present
    # We'll add it back conditionally based on the config
    has_none_union = " | None" in base_type
    if has_none_union:
        base_type = base_type.replace(" | None", "")

    # Check if this parameter is nullable from the config
    # Default is False (matching IntegerParameter and RealParameter default behavior)
    is_nullable = False
    if config_parser and section_name and param_name:
        try:
            is_nullable = config_parser.getboolean(section_name, f"{param_name}.nullable")
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            # If not specified in config, default to False (not nullable)
            is_nullable = False
    else:
        # No config provided, fall back to the type annotation's nullable info
        is_nullable = has_none_union

    # Add | None if parameter is nullable
    if is_nullable and base_type not in ("Any", "Optional[Any]"):
        if not base_type.startswith("Optional["):
            return f"{base_type} | None"

    return base_type


def _indent(text: str, level: int = 1, spaces: int = 4) -> str:
    pad = " " * (level * spaces)
    return "\n".join(pad + line if line.strip() else line for line in text.splitlines())


def _generate_parameter_type_stubs() -> str:
    """Automatically generate type stubs for all Parameter subclasses"""
    # Import the config module to analyze the actual classes
    config_mod = importlib.import_module("cea.config")
    Parameter = config_mod.Parameter

    # Get all Parameter subclasses
    param_classes = []
    for name in dir(config_mod):
        obj = getattr(config_mod, name)
        if inspect.isclass(obj) and issubclass(obj, Parameter) and obj != Parameter:
            param_classes.append(name)
    
    # Sort for consistent output
    param_classes.sort()
    
    # Generate stub declarations
    stubs = []
    for class_name in param_classes:
        stubs.append(f"class {class_name}(Parameter): ...")
    
    return "\n".join(stubs)


def _generate_nested_class_stub(nested_class: type) -> List[str]:
    """Generate stub for a nested class by inspecting it"""
    class_name = nested_class.__name__

    # Get attributes with type hints if available
    attributes = []
    if hasattr(nested_class, '__annotations__'):
        for attr_name, attr_type in nested_class.__annotations__.items():
            type_str = _ann_to_stub_str(attr_type)
            attributes.append(f"{attr_name}: {type_str}")

    # Infer attributes from __init__ if no annotations
    if not attributes and hasattr(nested_class, '__init__'):
        try:
            sig = inspect.signature(nested_class.__init__)
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                if param.annotation != param.empty:
                    type_str = _ann_to_stub_str(param.annotation)
                    attributes.append(f"{param_name}: {type_str}")
                else:
                    attributes.append(f"{param_name}: Any")
        except Exception:
            pass

    # Get methods
    methods = []
    for name in dir(nested_class):
        if name.startswith('_') and name not in ['__init__', '__enter__', '__exit__', '__repr__', '__str__']:
            continue
        attr = getattr(nested_class, name)
        if inspect.ismethod(attr) or inspect.isfunction(attr):
            try:
                sig = inspect.signature(attr)
                params = []
                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue
                    param_str = param_name
                    if param.annotation != param.empty:
                        type_str = _ann_to_stub_str(param.annotation)
                        param_str += f": {type_str}"
                    if param.default != param.empty:
                        param_str += " = ..."
                    params.append(param_str)

                # Special case return types for known methods
                if name == "__init__":
                    return_annotation = " -> None"
                elif name == "__enter__":
                    # Return self for context manager __enter__
                    # Use quotes for forward reference with noqa comment for nested classes
                    return_annotation = f" -> '{class_name}'"
                    method_str = f"def {name}({', '.join(['self'] + params)}){return_annotation}: ...  # noqa: F821"
                    methods.append(method_str)
                    continue
                elif name == "__exit__":
                    return_annotation = " -> None"
                elif name == "__repr__":
                    return_annotation = " -> str"
                elif name in ("apply", "clear", "unapply"):
                    # Common context manager methods
                    return_annotation = " -> None"
                elif sig.return_annotation != sig.empty:
                    return_annotation = f" -> {_ann_to_stub_str(sig.return_annotation)}"
                else:
                    return_annotation = " -> Any"

                methods.append(f"def {name}({', '.join(['self'] + params)}){return_annotation}: ...")
            except Exception:
                methods.append(f"def {name}(self, *args, **kwargs) -> Any: ...")

    # Build class definition
    result = [f"class {class_name}:"]
    if attributes:
        result.extend([f"    {attr}" for attr in attributes])
    if methods:
        result.extend([f"    {method}" for method in methods])
    if not attributes and not methods:
        result.append("    pass")

    return result


def _generate_configuration_class_stub(section_attrs: List[str], general_params: List[str], section_overloads: List[str], general_overloads: List[str]) -> str:
    """Automatically generate Configuration class stub by inspecting the actual class"""
    config_mod = importlib.import_module("cea.config")
    Configuration = config_mod.Configuration

    # Detect nested classes
    nested_classes = []
    for name in dir(Configuration):
        attr = getattr(Configuration, name)
        if inspect.isclass(attr) and attr.__module__ == Configuration.__module__:
            # This is a nested class defined within Configuration
            nested_classes.append(attr)

    # Get public methods from Configuration class
    # Skip __getattr__ since we'll add overloads for it
    methods = []
    for name in dir(Configuration):
        # Skip __getattr__ - we'll handle it separately with overloads
        if name == '__getattr__':
            continue
        if not name.startswith('_') or name in ['__init__', '__setattr__']:
            attr = getattr(Configuration, name)
            if inspect.ismethod(attr) or inspect.isfunction(attr):
                try:
                    sig = inspect.signature(attr)
                    # Convert signature to stub format
                    params = []
                    for param_name, param in sig.parameters.items():
                        if param_name == 'self':
                            continue
                        param_str = param_name
                        if param.annotation != param.empty:
                            ann_str = _ann_to_stub_str(param.annotation)
                            param_str += f": {ann_str}"
                        if param.default != param.empty:
                            param_str += " = ..."
                        params.append(param_str)

                    # Special case return types for known methods
                    if name == "__init__":
                        return_annotation = " -> None"
                    elif name == "__setattr__":
                        return_annotation = " -> None"
                    elif sig.return_annotation != sig.empty:
                        ann_str = _ann_to_stub_str(sig.return_annotation)
                        return_annotation = f" -> {ann_str}"
                    else:
                        return_annotation = " -> Any"

                    methods.append(f"def {name}({', '.join(['self'] + params)}){return_annotation}: ...")
                except Exception:
                    methods.append(f"def {name}(self, *args, **kwargs) -> Any: ...")

    # Core attributes
    attributes = [
        "# Core configuration attributes",
        "default_config: configparser.ConfigParser",
        "user_config: configparser.ConfigParser",
        "sections: Dict[str, Section]",
        "restricted_to: Optional[List[str]]",
        "",
        "# Known sections from default.config with typed section classes"
    ]

    if section_attrs:
        attributes.extend(section_attrs)

    if general_params:
        attributes.extend(["", "# Common general section parameters (frequently accessed)"] + general_params)

    # Generate nested class stubs dynamically
    nested_class_stubs = []
    if nested_classes:
        nested_class_stubs.append("")
        nested_class_stubs.append("# Nested classes")
        for nested_class in nested_classes:
            nested_class_stubs.extend(_generate_nested_class_stub(nested_class))

    # Build content with proper ordering: attributes, nested classes, overloads, then methods
    all_content = attributes + nested_class_stubs + [""]

    # Add overloads BEFORE methods (proper stub file ordering)
    overload_content = []
    if section_overloads:
        overload_content.extend(["# Overloads for specific section access"] + section_overloads + [""])

    if general_overloads:
        overload_content.extend(["# Overloads for general section parameter access"] + general_overloads + [""])

    # Add the catch-all __getattr__ implementation after all overloads
    if section_overloads or general_overloads:
        overload_content.append("def __getattr__(self, item: str) -> Union['Section', Any]: ...")

    all_content.extend(overload_content + [""] + methods)

    return "\n".join([
        "class Configuration:",
        _indent("\n".join(all_content))
    ])


def _generate_section_class_stub() -> str:
    """Automatically generate Section class stub by inspecting the actual class"""
    config_mod = importlib.import_module("cea.config")
    Section = config_mod.Section

    # Get public methods from Section class
    methods = []
    for name in dir(Section):
        if not name.startswith('_') or name in ['__init__', '__getattr__', '__setattr__', '__repr__']:
            attr = getattr(Section, name)
            if inspect.ismethod(attr) or inspect.isfunction(attr):
                try:
                    sig = inspect.signature(attr)
                    # Convert signature to stub format
                    params = []
                    for param_name, param in sig.parameters.items():
                        if param_name == 'self':
                            continue
                        param_str = param_name
                        if param.annotation != param.empty:
                            ann_str = _ann_to_stub_str(param.annotation)
                            param_str += f": {ann_str}"
                        if param.default != param.empty:
                            param_str += " = ..."
                        params.append(param_str)

                    # Special case return types for known methods
                    if name == "__init__":
                        return_annotation = " -> None"
                    elif name == "__repr__":
                        return_annotation = " -> str"
                    elif name == "__setattr__":
                        return_annotation = " -> None"
                    elif sig.return_annotation != sig.empty:
                        ann_str = _ann_to_stub_str(sig.return_annotation)
                        return_annotation = f" -> {ann_str}"
                    else:
                        return_annotation = " -> Any"

                    methods.append(f"def {name}({', '.join(['self'] + params)}){return_annotation}: ...")
                except Exception:
                    methods.append(f"def {name}(self, *args, **kwargs) -> Any: ...")
    
    attributes = [
        "name: str",
        "config: Configuration",
        "parameters: Dict[str, Parameter]"
    ]
    
    return "\n".join([
        "class Section:",
        _indent("\n".join(attributes + [""] + methods))
    ])


def _generate_parameter_class_stub() -> str:
    """Automatically generate Parameter class stub by inspecting the actual class"""
    config_mod = importlib.import_module("cea.config")
    Parameter = config_mod.Parameter

    # Get public methods from Parameter class
    methods = []
    for name in dir(Parameter):
        if not name.startswith('_') or name in ['__init__', '__repr__']:
            attr = getattr(Parameter, name)
            if inspect.ismethod(attr) or inspect.isfunction(attr):
                try:
                    sig = inspect.signature(attr)
                    # Convert signature to stub format
                    params = []
                    for param_name, param in sig.parameters.items():
                        if param_name == 'self':
                            continue
                        param_str = param_name
                        if param.annotation != param.empty:
                            ann_str = _ann_to_stub_str(param.annotation)
                            param_str += f": {ann_str}"
                        if param.default != param.empty:
                            param_str += " = ..."
                        params.append(param_str)

                    # Special case return types for known methods
                    if name == "__init__":
                        return_annotation = " -> None"
                    elif name == "__repr__":
                        return_annotation = " -> str"
                    elif name == "encode":
                        return_annotation = " -> str"
                    elif name == "get_raw":
                        return_annotation = " -> str"
                    elif name == "replace_references":
                        return_annotation = " -> str"
                    elif name in ("set", "initialize"):
                        return_annotation = " -> None"
                    elif sig.return_annotation != sig.empty:
                        ann_str = _ann_to_stub_str(sig.return_annotation)
                        return_annotation = f" -> {ann_str}"
                    else:
                        return_annotation = " -> Any"

                    methods.append(f"def {name}({', '.join(['self'] + params)}){return_annotation}: ...")
                except Exception:
                    methods.append(f"def {name}(self, *args, **kwargs) -> Any: ...")
    
    attributes = [
        "name: str",
        "section: Section",
        "fqname: str",
        "config: Configuration",
        "help: str",
        "category: Optional[str]"
    ]
    
    return "\n".join([
        "class Parameter:",
        _indent("\n".join(attributes + [""] + methods))
    ])


def _build_section_class(section_name: str, param_attrs: List[str], param_overloads: List[str]) -> str:
    attr_name = section_name.replace("-", "_")
    class_name = f"{attr_name.title().replace('_', '')}Section"

    body_lines: List[str] = [f'"""Typed section for {section_name} configuration"""']
    if param_attrs:
        body_lines.extend(param_attrs)

    # Add overloads if any, followed by catch-all __getattr__
    if param_overloads:
        body_lines.append("")  # blank line before overloads
        # Only use @overload decorator if there are 2 or more overloads
        # Single overload is invalid per PEP 484
        if len(param_overloads) == 1:
            # Don't add overload decorator, just add the catch-all
            body_lines.append("def __getattr__(self, item: str) -> Any: ...")
        else:
            # Multiple overloads - use @overload decorator
            body_lines.extend(param_overloads)
            body_lines.append("def __getattr__(self, item: str) -> Any: ...")
    elif not param_attrs:
        # Only add pass if there are no attributes and no overloads
        body_lines.append("pass")

    return "\n".join([f"class {class_name}(Section):", _indent("\n".join(body_lines))])


def _get_module_level_constants() -> List[str]:
    """Extract module-level constants from cea.config"""
    config_mod = importlib.import_module("cea.config")

    constants = []
    for name in dir(config_mod):
        # Skip private/dunder attributes and imported modules
        if name.startswith('_'):
            continue

        obj = getattr(config_mod, name)

        # Skip classes, functions, and imported modules
        if inspect.isclass(obj) or inspect.isfunction(obj) or inspect.ismodule(obj):
            continue

        # Only include uppercase constants (Python convention)
        if name.isupper():
            # Infer type from the value
            if isinstance(obj, str):
                type_hint = "str"
            elif isinstance(obj, int):
                type_hint = "int"
            elif isinstance(obj, float):
                type_hint = "float"
            elif isinstance(obj, bool):
                type_hint = "bool"
            else:
                type_hint = "Any"

            constants.append(f"{name}: {type_hint}")

    return constants


def generate_config_stub():
    """Generate comprehensive type stub file for cea.config"""

    # Path to default.config (in cea/ directory, one level up from utilities/)
    default_config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "default.config")
    # Path to config.pyi (also in cea/ directory)
    stub_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.pyi")

    if not os.path.exists(default_config_path):
        print(f"Error: {default_config_path} not found")
        return

    config_parser = configparser.ConfigParser()
    config_parser.read(default_config_path)

    # Extract module-level constants
    module_constants = _get_module_level_constants()

    section_classes: List[str] = []
    section_attrs: List[str] = []

    for section_name in config_parser.sections():
        attr_name = section_name.replace("-", "_")
        class_name = f"{attr_name.title().replace('_', '')}Section"

        param_attrs: List[str] = []
        for param_name in config_parser.options(section_name):
            if "." in param_name:
                continue
            param_type = config_parser.get(
                section_name, f"{param_name}.type", fallback="StringParameter"
            )
            param_attr = param_name.replace("-", "_")
            annotation = infer_type_from_param_class_name(param_type, section_name, param_name, config_parser)
            param_attrs.append(f"{param_attr}: {annotation}")

        param_overloads: List[str] = []
        for param_name in config_parser.options(section_name):
            if "." in param_name:
                continue
            param_type = config_parser.get(
                section_name, f"{param_name}.type", fallback="StringParameter"
            )
            param_attr = param_name.replace("-", "_")
            annotation = infer_type_from_param_class_name(param_type, section_name, param_name, config_parser)
            param_overloads.append(
                f'@overload\ndef __getattr__(self, item: Literal["{param_attr}"]) -> {annotation}: ...'
            )

        section_classes.append(
            _build_section_class(section_name, param_attrs, param_overloads)
        )
        section_attrs.append(f"{attr_name}: {class_name}")

    # general params
    general_params: List[str] = []
    if "general" in config_parser.sections():
        for param_name in config_parser.options("general"):
            if "." in param_name:
                continue
            param_type = config_parser.get(
                "general", f"{param_name}.type", fallback="StringParameter"
            )
            attr_name = param_name.replace("-", "_")
            annotation = infer_type_from_param_class_name(param_type, "general", param_name, config_parser)
            general_params.append(f"{attr_name}: {annotation}")

    section_overloads: List[str] = []
    for section_name in config_parser.sections():
        attr_name = section_name.replace("-", "_")
        class_name = f"{attr_name.title().replace('_', '')}Section"
        section_overloads.append(
            f'@overload\ndef __getattr__(self, item: Literal["{attr_name}"]) -> {class_name}: ...'
        )

    general_overloads: List[str] = []
    if "general" in config_parser.sections():
        for param_name in config_parser.options("general"):
            if "." in param_name:
                continue
            param_type = config_parser.get(
                "general", f"{param_name}.type", fallback="StringParameter"
            )
            attr_name = param_name.replace("-", "_")
            annotation = infer_type_from_param_class_name(param_type, "general", param_name, config_parser)
            general_overloads.append(
                f'@overload\ndef __getattr__(self, item: Literal["{attr_name}"]) -> {annotation}: ...'
            )

    # Assemble stub content
    parts: List[str] = [
        "# Type stub file for cea.config",
        "# Auto-generated from default.config - do not edit manually",
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any, Dict, List, Union, Optional, Generator, Tuple, overload, Literal",
        "import configparser",
        "",
    ]

    # Add module-level constants if any
    if module_constants:
        parts.extend([
            "# Module-level constants",
            *module_constants,
            "",
        ])

    parts.extend([
        _generate_configuration_class_stub(section_attrs, general_params, section_overloads, general_overloads),
        "",
        _generate_section_class_stub(),
        "",
        "# Typed section classes with parameter annotations",
        "\n\n".join(section_classes),
        "",
        _generate_parameter_class_stub(),
        "",
        "# Parameter type classes for better type hints",
        _generate_parameter_type_stubs(),
        "",
        "def config_identifier(python_identifier: str) -> str: ...",
        "",
    ])

    stub_content = "\n".join(parts)

    with open(stub_path, "w") as f:
        f.write(stub_content)

    print(f"Generated type stub at {stub_path}")
    print(f"Found {len(config_parser.sections())} sections")


if __name__ == "__main__":
    generate_config_stub()
