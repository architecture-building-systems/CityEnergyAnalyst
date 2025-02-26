import datetime
import os.path
import re
import subprocess

import cea.config

init_path = os.path.join(os.path.dirname(__file__), "..", "__init__.py")
credits_path = os.path.join(os.path.dirname(__file__), "..", "..", "CREDITS.md")
changelog_path = os.path.join(os.path.dirname(__file__), "..", "..", "CHANGELOG.md")
version_pattern = re.compile(r'__version__ = "(\d+\.\d+\.\d+)"')


def replace_version(new_version: str):
    with open(init_path) as f:
        init = f.read()

    if not version_pattern.search(init):
        raise ValueError("Unable to find match, check if __version__ is found in cea/__init__.py")
    result = version_pattern.sub(f'__version__ = "{new_version}"', init)

    with open(init_path, "w") as f:
        f.write(result)


def update_credits(current_version: str, new_version: str):
    contributors_template_path = os.path.join(os.path.dirname(__file__), "contributors_template")
    with open(contributors_template_path) as f:
        contributors = f.read()

    credits_pattern = re.compile(rf"(<!-- credits -->)\n.*(- Version ({current_version}|.+) - .+)\n", re.MULTILINE)

    date_today = datetime.datetime.today()
    new_version_line = f"- Version {new_version} - {date_today.strftime('%B %Y')}"
    replacement = rf"\1\n" \
                  f"{new_version_line}\n" \
                  f"\n" \
                  f"{contributors}\n" \
                  f"\n" \
                  rf"\2\n"

    with open(credits_path, "r") as f:
        _credits = f.read()

    if not credits_pattern.search(_credits):
        raise ValueError("Unable to find match, check if <!-- credits --> is found in CREDITS.md")
    result = credits_pattern.sub(replacement, _credits, count=1)

    with open(credits_path, "w") as f:
        f.write(result)


def update_changelog() -> None:
    try:
        subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], check=True, capture_output=True,
                       cwd=os.path.dirname(__file__))
    except subprocess.CalledProcessError:
        raise Exception("Current CEA directory is not a git repository.")

    changelog_script_path = os.path.join(os.path.dirname(__file__), "..", "..", "bin", "create-changelog.py")
    result = subprocess.run(["python", changelog_script_path], check=True, capture_output=True,
                            cwd=os.path.dirname(__file__))
    changelog = result.stdout.decode()

    with open(changelog_path, "w") as f:
        f.write(changelog)


def main(config: cea.config.Configuration) -> None:
    from cea import __version__
    current_version = __version__

    new_version = config.development.release_version

    print(f"Current version: {current_version}")
    print(f"New version: {new_version}")

    if not re.match(r"\d+\.\d+\.\d+", new_version):
        raise ValueError("Version number needs to be in Semantic Versioning format. e.g., 1.0.0")
    if current_version == new_version:
        print(f"New version is the same as the current version ({new_version}). Ignoring update.")
        return

    print("Updating Changelog")
    update_changelog()

    print("Updating Credits")
    update_credits(current_version, new_version)

    print("Updating Version")
    replace_version(new_version)


if __name__ == "__main__":
    cea_config = cea.config.Configuration()

    main(cea_config)
