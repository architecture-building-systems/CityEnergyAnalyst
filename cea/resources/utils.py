import cea_external_tools


def get_radiation_bin_path() -> str | None:
    """
    Get the path to radiation binaries from cea_external_tools.

    :return: The path to binaries, or None if not found.
    """
    return cea_external_tools.get_bin_path()
