__version__ = "2.19"


class ConfigError(Exception):
    """Raised when the configuration of a tool contains some invalid values."""
    rc = 100  # sys.exit(rc)


class CustomDatabaseNotFound(Exception):
    """Raised when the InputLocator can't find a user-provided database (region=='custom')"""
    rc = 101  # sys.exit(rc)


class ScriptNotFoundException(Exception):
    """Raised when an invalid script name is used."""
    rc = 102  # sys.exit(rc)


class MissingInputDataException(Exception):
    """Raised when a script can't run because some information is missing"""
    rc = 103


class InvalidOccupancyNameException(Exception):
    """Raised when the occupancy.dbf has an invalid / unknown occupancy column"""
    rc = 104