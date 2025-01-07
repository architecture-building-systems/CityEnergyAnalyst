:orphan:

schemas.yml
###########
The `schemas.yml` file is used to describe the input/output files used in CEA.

e.g.
::

    get_database_construction_standards:
      created_by: [database-helper]
      file_path: inputs/technology/archetypes/CONSTRUCTION_STANDARDS.xlsx
      file_type: xlsx
      schema:
        STANDARD_DEFINITION:
          columns:
            STANDARD:
              type: string
              primary: true
            Description:
              type: string
            YEAR_START:
              type: int
              min: 0
            YEAR_END:
              type: int
              min: 0
          constraints:
            YEAR:
              YEAR_START < YEAR_END
        used_by: []

Each file is represented by a key that is the name of the InputLocator method that points to it.

It provides other information of the file based on these set of properties:
    - created_by
        - lists which script creates this file. This is used to suggest scripts when input files
          (as defined in ``scripts.yml``) are missing.
    - file_path
        - path where the file can be found relative to the path of the scenario
        - arguments to the locator method are replaced in the string
          (e.g. ``outputs/data/solar-radiation/{building}_radiation.csv``)
    - file_type
        - type of file (extension) - indicates the parser to use to read the data found in the file
          (one of ``{xls, xlsx, csv, dbf, shp, json}``)
    - schema
        - describes the data structure of the file and how it interacts with data from other files
    - used_by
        - lists which script uses this file.

File type
+++++++++

``file_type`` affects how CEA parses the information found in the ``schema`` property.

This is because some file types contain more than one table in them.
e.g. excel files usually contain multiple tables depending on the number of sheets that it has
while .csv/.dbf files usually only contain one table.

To workaround this, the level of keys found in ``schema`` is be different based on its type,
where the table name for multiple table type files encapsulate each ``schema`` properties
as found in single table type files.

e.g. single table type files
::


    $locator_method_name:
      file_type: csv
      schema:
        columns:
            $column_name:
                $column_properties
        constraints:
            $constraints


e.g. multiple table type files
::


    $locator_method_name:
      schema:
        file_type: xlsx
        $table_name:
            columns:
                $column_name:
                    $column_properties
            constraints:
                $constraints


Schema
++++++

The ``schema`` of the file is be separated into two sections: ``columns`` and ``constraints``.

(for Excel files, each worksheet has these two sections as explained above)

Columns Property
================

The schema stores information regarding the values found in the columns of the given data and is described by giving
the expected type of value.

This information is be used by the ``InputValidator`` class to validate each value found in the column.

Currently the schema supports these types:

    - ``string``
    - ``float``
    - ``int``
    - Choice
    - ``boolean``

Each of these types will inherit from a set of base properties.

Base Properties
---------------

Properties:

- Non-nullable. Value cannot be empty
    prop nullable: false (default)

String type
------------

Inherits from Base Properties.

Properties:

- Regex. Value matches the given regular expression
    prop regex: None (default)

Numeric type
------------

Inherits from Base Properties.

Tests:

- Checks if value is an instance of int, long or float

Properties:

- Minimum. Value cannot be less than given value
    prop min: None (default)

- Maximum. Value cannot be more than given value
    prop max: None (default)

Float type
------------

Inherits from Numeric Properties.

Integer type
------------

Inherits from Numeric Properties.

Tests:

- Checks if value is an instance of int, long and not float to prevent loss of precision

Choice type
------------

Inherits from Base Properties.

Tests:

- Checks if value is found in a list of values based on the properties set below

- Values. Given list of valid values
    prop values: None (default)

- lookup. List of valid values based on other databases
    lookup prop will need to have a list of properties as a pointer to allow it to find the required list of values:
        - path: locator method for the database referenced
        - sheet: location of table if applicable
        - column: column of table from which to get list of values

    prop lookup: None (default)

Boolean type
------------

Inherits from Base Properties.


Tests:

- Checks if value is an instance of boolean (i.e. True or False)

Constraints Property
====================
Besides column-based validation, the schema also provides a simple* row-based validation using the constraints property.

Provide a property as the name of the constraint and enter a boolean expression with column names of the table

e.g.
::

    constraints:
        YEAR:
            YEAR_START < YEAR_END
