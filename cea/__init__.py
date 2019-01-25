__version__ = "2.9.2"


class ConfigError(Exception):
    """Raised when the configuration of a tool contains some invalid values."""
    rc = 100  # sys.exit(rc)


class CustomDatabaseNotFound(Exception):
    """Raised when the InputLocator can't find a user-provided database (region=='custom')"""
    rc = 101  # sys.exit(rc)


class ScriptNotFoundException(Exception):
    """Raised when an invalid script name is used."""
    rc = 102  # sys.exit(rc)