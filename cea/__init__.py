__version__ = "2.7.18"


class ConfigError(Exception):
    """Raised when the configuration of a tool contains some invalid values."""
    rc = 100  # sys.exit(rc)


class CustomDatabaseNotFound(Exception):
    """Raised when the InputLocator can't find a user-provided database (region=='custom')"""
    rc = 101  # sys.exit(rc)