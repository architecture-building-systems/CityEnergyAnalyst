__version__ = "2.7.8"


class ConfigError(Exception):
    """Raised when the configuration of a tool contains some invalid values."""
    rc = 100  # sys.exit(rc)
