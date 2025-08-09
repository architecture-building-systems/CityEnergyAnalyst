import os


def get_site_package_radiation_bin_path() -> str | None:
    """
    Get the path to radiation binaries in the site-packages directory.

    :return: The path to binaries, or None if not found.
    """
    import site
    for site_packages_dir in site.getsitepackages():
        daysim_path = os.path.join(site_packages_dir, "cea", "radiation", "bin")
        if os.path.exists(daysim_path):
            return daysim_path

    return None