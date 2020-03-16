Column Property
======================
The schema will validate column values based on the type specified for that column

Currently the schema supports types:
    - String
    - Numeric (Float and Integer)
    - Choice
    - Boolean

which the `InputFileValidator` class would use to validate using `Validator` classes.

Base type
------------

Each type will inherit from a set of base properties listed here

Properties:

- Non-nullable. Value cannot be empty
    prop nullable: false (default)

String type
------------

Properties:

- Regex. Value matches the given regular expression
    prop regex: None (default)

Numeric type
------------

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

Tests:

- Checks if value is an instance of boolean (i.e. True or False)

Constraints Property
====================
Besides column-based validation, the schema also provides a simple* row-based validation using the constraints property.

Provide a property as the name of the constraint and enter a boolean expression with column names of the table

e.g.

constraints:
    YEAR:
        YEAR_START < YEAR_END
