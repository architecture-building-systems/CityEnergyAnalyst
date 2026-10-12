"""Check that the packages installed in the Docker image match pixi.lock.

Runs inside the built image (pyyaml is part of the environment), so the CI runner needs no pixi.

    python check_image_lock_parity.py /path/to/pixi.lock

Exits 1 if a package in WATCHLIST differs from the lock. Other differences are printed as warnings.
"""
import re
import sys
from importlib.metadata import distributions

import yaml

# the web stack plus numpy: a silent difference here is what broke the demo endpoint in prod
WATCHLIST = {
    "fastapi", "starlette", "uvicorn", "pydantic", "pydantic-core", "sqlmodel", "sqlalchemy", "numpy",
}
# installed by the Dockerfile on top of the lock (--no-deps), so not part of it
IGNORED = {"cityenergyanalyst"}


def normalise(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def locked_packages(lock_path: str) -> dict[str, str]:
    """Name -> version of every PyPI package, plus the watchlist packages that come from conda."""
    with open(lock_path) as f:
        lock = yaml.safe_load(f)

    platform = next(p["name"] for p in lock["platforms"] if p.get("subdir") == "linux-64")
    entries = lock["environments"]["default"]["packages"][platform]
    urls = {entry.get("pypi") or entry["conda"] for entry in entries}

    packages = {}
    for package in lock["packages"]:
        url = package.get("pypi") or package.get("conda")
        if url not in urls:
            continue
        if "pypi" in package:
            packages[normalise(package["name"])] = package["version"]
        else:
            # conda entries carry no name or version field: the file name is <name>-<version>-<build>
            name, version, _build = url.rsplit("/", 1)[-1].rsplit("-", 2)
            if normalise(name) in WATCHLIST:
                packages[normalise(name)] = version
    return packages


def installed_packages() -> dict[str, str]:
    return {normalise(d.metadata["Name"]): d.version for d in distributions()}


def main(lock_path: str) -> int:
    locked = locked_packages(lock_path)
    installed = installed_packages()

    failures = []
    for name, version in sorted(locked.items()):
        if name in IGNORED:
            continue
        if installed.get(name) != version:
            message = f"{name}: locked {version}, image has {installed.get(name)}"
            if name in WATCHLIST:
                failures.append(message)
            else:
                print(f"warning: {message}")

    for name in sorted(WATCHLIST - set(locked)):
        failures.append(f"{name}: missing from the lock")

    for message in failures:
        print(f"error: {message}")
    print(f"checked {len(locked)} locked packages, {len(failures)} watchlist failures")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
