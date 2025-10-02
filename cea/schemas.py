"""
Maintain access to the schemas (input- and output file descriptions) used by the CEA. These are stored in the
``schemas.yml`` file. Reading it is supposed to be done through the :py:func:`cea.schemas.schemas`. The plugins
parameter allows reading in schemas from ``schemas.yml`` files defined in plugins.
"""

import abc
import os
from typing import Any, List, Optional, Dict

import yaml
import warnings
import functools

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2020, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# keep a cache of schemas.yml - this will never change so avoid re-reading it.
# since we can actually call schemas with a varying list of plugins, store the resulting schemas dict
# in a dict indexed by the

__schemas = {}


def schemas(plugins: Optional[List] = None) -> Dict:
    """Return the contents of the schemas.yml file
    :parameter plugins: the list of plugins to generate the schemas for. Use ``config.plugins`` for this.
    :type plugins: List[cea.plugin.CeaPlugin]
    """
    if plugins is None:
        plugins = []

    # loading schemas.yml is quite expensive - try to avoid it as much as possible by
    # maintaining a cache of the schemas - using the plugin list as a key
    global __schemas
    key = ":".join(str(p) for p in plugins)

    if key not in __schemas:
        schemas_yml = os.path.join(os.path.dirname(__file__), 'schemas.yml')
        with open(schemas_yml, "r") as f:
            schemas_dict = yaml.load(f, Loader=yaml.CLoader)
        __schemas[key] = schemas_dict

        # add the plugins - these don't use caches as their schemas.yml are (probably) much shorter
        for plugin in plugins:
            if plugin.schemas is not None:
                __schemas[key].update(plugin.schemas)
    return __schemas[key]


def get_schema_variables(schema):
    """
    This method returns a set of all variables within the schemas.yml. The set is organised by:
    (variable_name, locator_method, script, file_name:sheet_name)
    If the variable is from an input database, the script is replaced by "-"
    Also, if the variable is not from a tree data shape (such as xlsx or xls), the 'file_name:sheet_name' becomes 'file_name' only.
    The sheet_name is important to consider as a primary key for each variable can only be made through combining the 'file_name:sheet_name' and
    'variable_name'. Along with the locator_method, the set should contain all information necessary for most tasks.
    """

    schema_variables = set()
    for locator_method in schema:

        # if there is no script mapped to 'created_by', it must be an input_file
        # replace non-existent script with the name of the file without the extension
        if not schema[locator_method]['created_by']:
            script = "-"
        else:
            script = schema[locator_method]['created_by'][0]

        if "schema" not in schema[locator_method] or not schema[locator_method]["schema"]:
            print("Could not find schema for {locator_method}".format(locator_method=locator_method))
            continue

        # for repetitive variables, include only one instance
        for variable in schema[locator_method]['schema']:
            if variable.find('srf') != -1:
                variable = variable.replace(variable, 'srf0')
            if variable.find('PIPE') != -1:
                variable = variable.replace(variable, 'PIPE0')
            if variable.find('NODE') != -1:
                variable = variable.replace(variable, 'NODE0')
            if variable.find('B0') != -1:
                variable = variable.replace(variable, 'B001')

            # if the variable is one associated with an epw file: exclude for now
            if schema[locator_method]['file_type'] == 'epw':
                variable = 'EPW file variables'

            # if the variable is actually a sheet name due to tree data shape
            if schema[locator_method]['file_type'] in {'xlsx', 'xls'}:
                worksheet = variable
                for variable_in_sheet in schema[locator_method]['schema'][worksheet]:
                    file_name = "{file_path}:{worksheet}".format(file_path=schema[locator_method]['file_path'],
                                                                 worksheet=worksheet)
                    schema_variables.add((variable_in_sheet, locator_method, script, file_name))
            # otherwise create the meta set
            else:

                file_name = schema[locator_method]['file_path']
                schema_variables.add((variable, locator_method, script, file_name))
    return schema_variables


def get_schema_scripts(plugins):
    """Returns the list of scripts actually mentioned in the schemas.yml file"""
    schemas_dict = schemas(plugins)
    schema_scripts = set()
    for locator_method in schemas_dict:
        if schemas_dict[locator_method]['used_by']:
            for script in schemas_dict[locator_method]['used_by']:
                schema_scripts.add(script)
        if schemas_dict[locator_method]['created_by'] > 0:
            for script in schemas_dict[locator_method]['created_by']:
                schema_scripts.add(script)
    return schema_scripts


def create_schema_io(locator, lm, schema, original_function=None):
    """
    Returns a wrapper object that can be used to replace original_function - the interface remains largely
    the same.
    :param cea.inputlocator.InputLocator locator: The locator we're attaching methods to.
    :param str lm: the name of the locator method being wrapped
    :param dict schema: the configuration of this locator method as defined in schemas.yml
    :param original_function: the original locator method - so we can call it. Created from schema["file_path"] if None
    :return: SchemaIo instance
    """
    if not original_function:
        original_function = create_locator_method(lm, schema)

    file_type = schema["file_type"]
    file_type_to_schema_io = {
        "csv": CsvSchemaIo,
        "dbf": DbfSchemaIo,
        "shp": ShapefileSchemaIo,
    }
    if file_type not in file_type_to_schema_io:
        # just return the default - no read() and write() possible
        return DefaultSchemaIo(locator, lm, schema, original_function)
    return file_type_to_schema_io[file_type](locator, lm, schema, original_function)


def create_locator_method(lm, schema):
    """
    Returns a function that works as an InputLocator method - it reads the
    :param str lm: the name of the locator method
    :param dict schema: the configuration of this locator method as defined in schemas.yml
    :return: the locator method (note, only kwargs are used, if at all)
    """
    file_path = schema["file_path"]

    def locator_method(self, *args, **kwargs):
        return os.path.join(self.scenario, file_path.format(**kwargs).replace("/", os.path.sep))

    locator_method.__name__ = lm
    locator_method.__doc__ = file_path
    return locator_method


class SchemaIo(abc.ABC):
    """A base class for reading and writing files using schemas.yml for validation
    The default just wraps the function - read() and write() will throw errors and should be implemented
    in subclasses
    """

    def __init__(self, locator, lm, schema, original_function):
        self.locator = locator
        self.lm = lm
        self.schema = schema
        self.original_function = original_function
        functools.update_wrapper(self, original_function)

    def __str__(self):
        return "<{class_name}({lm}): {doc}>".format(class_name=self.__class__.__name__, lm=self.lm,
                                                    doc=self.original_function.__doc__)

    def __repr__(self):
        return "<{class_name}({lm}): {doc}>".format(class_name=self.__class__.__name__, lm=self.lm,
                                                    doc=self.original_function.__doc__)

    def __call__(self, *args, **kwargs):
        return self.original_function(self.locator, *args, **kwargs)

    @abc.abstractmethod
    def read(self, *args, **kwargs):
        """
        Open the file indicated by the locator method and return it as a Dataframe.
        args and kwargs are passed to the original (undecorated) locator method to figure out the location of the
        file.

        :param args:
        :param kwargs:
        :rtype: pd.DataFrame
        """
        raise AttributeError("{lm}: don't know how to read file_type {file_type}".format(
            lm=self.lm, file_type=self.schema["file_type"]))

    @abc.abstractmethod
    def write(self, df, *args, **kwargs):
        raise AttributeError("{lm}: don't know how to write file_type {file_type}".format(
            lm=self.lm, file_type=self.schema["file_type"]))

    def new(self) -> Any:
        raise AttributeError("{lm}: don't know how to create a new Dataframe for file_type {file_type}".format(
            lm=self.lm, file_type=self.schema["file_type"]))

    def validate(self, df):
        """Check to make sure the Dataframe conforms to the schema"""
        expected_columns = set(self.schema["schema"]["columns"].keys())
        found_columns = set(df.columns.values)

        # handle some extra cases
        if "PIPE0" in expected_columns:
            found_columns = {c for c in found_columns if not c.startswith("PIPE")}
            found_columns.add("PIPE0")

        # handle some extra cases
        if "NODE0" in expected_columns:
            found_columns = {c for c in found_columns if not c.startswith("NODE")}
            found_columns.add("NODE0")

        if not found_columns == expected_columns:
            missing_columns = expected_columns - found_columns
            extra_columns = found_columns - expected_columns

            warnings.warn("Dataframe does not conform to schemas.yml specification for {lm}"
                          "(missing: {missing_columns}, extra: {extra_columns}".format(
                lm=self.lm, missing_columns=missing_columns, extra_columns=extra_columns))

    def colors(self):
        """
        Returns the colors for the columns in the schema, defaulting to black if not specified. Result is a dict
        mapping column name to "rgb(219, 64, 82)" format as used in plotly.

        Note that schemas.yml specifies colors using names taken from
        :type: Dict[str, str]
        """
        from .plots.colors import color_to_rgb

        result = {}
        columns = self.schema["schema"]["columns"]
        for column in columns.keys():
            result[column] = color_to_rgb(columns[column].get("plot-color", "black"))
        return result

class DefaultSchemaIo(SchemaIo):
    """Read and write default files - and attempt to validate them."""

    def read(self, *args, **kwargs):
        super().read(*args, **kwargs)

    def write(self, df, *args, **kwargs):
        super().write(df, *args, **kwargs)

    def new(self):
        super().new()


class CsvSchemaIo(SchemaIo):
    """Read and write csv files - and attempt to validate them."""

    def read(self, *args, **kwargs):
        """
        Open the file indicated by the locator method and return it as a Dataframe.
        args and kwargs are passed to the original (undecorated) locator method to figure out the location of the
        file.

        :param args:
        :param kwargs:
        :rtype: pd.DataFrame
        """
        import pandas as pd

        df = pd.read_csv(self(*args, **kwargs))
        self.validate(df)
        return df

    def write(self, df, *args, **kwargs):
        """
        :type df: pd.Dataframe
        """
        self.validate(df)
        csv_args = {}
        if "float_format" in self.schema:
            csv_args["float_format"] = self.schema["float_format"]
        path_to_csv = self(*args, **kwargs)
        parent_folder = os.path.dirname(path_to_csv)
        if not os.path.exists(parent_folder):
            os.makedirs(parent_folder)
        df.to_csv(path_to_csv, index=False, **csv_args)

    def new(self):
        import pandas as pd

        return pd.DataFrame(columns=(self.schema["schema"]["columns"].keys()))


class DbfSchemaIo(SchemaIo):
    """Read and write .dbf files - and attempt to validate them."""

    def read(self, *args, **kwargs):
        """
        Open the file indicated by the locator method and return it as a DataFrame.
        args and kwargs are passed to the original (undecorated) locator method to figure out the location of the
        file.

        :param args:
        :param kwargs:
        :rtype: pd.DataFrame
        """
        from cea.utilities.dbf import dbf_to_dataframe
        df = dbf_to_dataframe(self(*args, **kwargs))
        self.validate(df)
        return df

    def write(self, df, *args, **kwargs):
        """
        :type df: pd.Dataframe
        """
        self.validate(df)
        from cea.utilities.dbf import dataframe_to_dbf
        path_to_dbf = self(*args, **kwargs)

        parent_folder = os.path.dirname(path_to_dbf)
        if not os.path.exists(parent_folder):
            os.makedirs(parent_folder)

        dataframe_to_dbf(df, path_to_dbf)


class ShapefileSchemaIo(SchemaIo):
    """Read and write .shp files - and attempt to validate them."""

    def read(self, *args, **kwargs):
        """
        Open the file indicated by the locator method and return it as a DataFrame.
        args and kwargs are passed to the original (undecorated) locator method to figure out the location of the
        file.

        :param args:
        :param kwargs:
        :rtype: geopandas.GeoDataFrame
        """

        # make sure it's in the correct projection
        from cea.utilities.standardize_coordinates import shapefile_to_WSG_and_UTM
        df, _, __ = shapefile_to_WSG_and_UTM(self(*args, **kwargs))
        self.validate(df)

        return df

    def write(self, df, *args, **kwargs):
        """
        :type df: geopandas.GeoDataFrame
        """
        from cea.utilities.standardize_coordinates import (get_lat_lon_projected_shapefile,
                                                           get_projected_coordinate_system)
        self.validate(df)
        path_to_shp = self(*args, **kwargs)

        parent_folder = os.path.dirname(path_to_shp)
        if not os.path.exists(parent_folder):
            os.makedirs(parent_folder)
        lat, lon = get_lat_lon_projected_shapefile(df)

        # get coordinate system and re project to UTM
        df = df.to_crs(get_projected_coordinate_system(lat, lon))

        df.to_file(path_to_shp)
