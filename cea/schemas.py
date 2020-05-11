"""
Maintain access to the schemas (input- and output file descriptions) used by the CEA. These are stored in the
``schemas.yml`` file. Reading it is supposed to be done through the :py:func:`cea.schemas.schemas`. The plugins
parameter allows reading in schemas from ``schemas.yml`` files defined in plugins.
"""

from __future__ import print_function
from __future__ import division

import os
import pandas as pd
import yaml
import warnings
import functools
from typing import List, Callable

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
# FIXME: actually... if we add in plugins it _might_ change...
__schemas = {}


def schemas(plugins):
    """Return the contents of the schemas.yml file
    :parameter plugins: the list of plugins to generate the schemas for. Use ``config.plugins`` for this.
    :type plugins: List[cea.plugin.CeaPlugin]
    """
    global __schemas
    key = ":".join(str(p) for p in plugins)
    if not key in __schemas:
        schemas_yml = os.path.join(os.path.dirname(__file__), 'schemas.yml')
        __schemas[key] = yaml.load(open(schemas_yml), Loader=yaml.CLoader)
        for plugin in plugins:
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

        if not "schema" in schema[locator_method] or not schema[locator_method]["schema"]:
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


def get_schema_scripts():
    """Returns the list of scripts actually mentioned in the schemas.yml file"""
    schemas_dict = schemas()
    schema_scripts = set()
    for locator_method in schemas_dict:
        if schemas_dict[locator_method]['used_by']:
            for script in schemas_dict[locator_method]['used_by']:
                schema_scripts.add(script)
        if schemas_dict[locator_method]['created_by'] > 0:
            for script in schemas_dict[locator_method]['created_by']:
                schema_scripts.add(script)
    return schema_scripts


def create_schema_io(lm, schema, original_function=None):
    """
    Returns a wrapper object that can be used to replace original_function - the interface remains largely
    the same.
    :param str lm: the name of the locator method being wrapped
    :param dict schema: the configuration of this locator method as defined in schemas.yml
    :param original_function: the original locator method - so we can call it. Created from schema["file_path"] if None
    :return: SchemaIo instance
    """
    if not original_function:
        original_function = create_locator_method(lm, schema)

    file_type = schema["file_type"]
    file_type_to_schema_io = {
        "csv": CsvSchemaIo
    }
    if file_type not in file_type_to_schema_io:
        # just return the default - no read() and write() possible
        return SchemaIo(lm, schema, original_function)
    return file_type_to_schema_io[file_type](lm, schema, original_function)


def create_locator_method(lm, schema):
    """
    Returns a function that works as an InputLocator method - it reads the
    :param cea.inputlocator.InputLocator self: The locator this method will be bound to`
    :param str lm: the name of the locator method
    :param dict schema: the configuration of this locator method as defined in schemas.yml
    :return: the locator method (note, only kwargs are used, if at all)
    """
    file_path = schema["file_path"]

    def locator_method(self, *args, **kwargs):
        return file_path.format(**kwargs)

    locator_method.func_name = lm
    locator_method.func_doc = file_path
    return locator_method


class SchemaIo(object):
    """A base class for reading and writing files using schemas.yml for validation
    The default just wraps the function - read() and write() will throw errors and should be implemented
    in subclasses
    """
    def __init__(self, lm, schema, original_function):
        self.lm = lm
        self.schema = schema
        self.original_function = original_function
        functools.update_wrapper(self, original_function)

    def __str__(self):
        return "<{class_name}({lm}): {doc}>".format(class_name=self.__class__.__name__, lm=self.lm,
                                                    doc=self.original_function.func_doc)

    def __repr__(self):
        return "<{class_name}({lm}): {doc}>".format(class_name=self.__class__.__name__, lm=self.lm,
                                                    doc=self.original_function.func_doc)

    def __call__(self, *args, **kwargs):
        return self.original_function(*args, **kwargs)

    def read(self, *args, **kwargs):
        raise AttributeError("{lm}: don't know how to read file_type {file_type}".format(
            lm=self.lm, file_type=self.schema["file_type"]))

    def write(self, df, *args, **kwargs):
        raise AttributeError("{lm}: don't know how to write file_type {file_type}".format(
            lm=self.lm, file_type=self.schema["file_type"]))


class CsvSchemaIo(SchemaIo):
    """Read and write csv files - and attempt to validate them."""
    def read(self, *args, **kwargs):
        df = pd.read_csv(self(*args, **kwargs))
        self.validate(df)
        return df

    def write(self, df, *args, **kwargs):
        """
        :type df: pd.Dataframe
        """
        self.validate(df)
        csvargs={}
        if "float_format" in self.schema:
            csvargs["float_format"] = self.schema["float_format"]
        df.to_csv(self(*args, **kwargs), index=False, **csvargs)

    def validate(self, df):
        """Check to make sure the Dataframe conforms to the schema"""
        expected_columns = set(self.schema["schema"]["columns"].keys())
        found_columns = set(df.columns.values)
        if not found_columns == expected_columns:
            missing_columns = expected_columns - found_columns
            extra_columns = found_columns - expected_columns
            warnings.warn("Dataframe does not conform to schemas.yml specification for {lm}"
                             "(missing: {missing_columns}, extra: {extra_columns}".format(
                lm=self.lm, missing_columns=missing_columns, extra_columns=extra_columns))






