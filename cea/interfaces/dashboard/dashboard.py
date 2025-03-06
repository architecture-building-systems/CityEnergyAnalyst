import os
import sys
import tempfile

import uvicorn

from cea.interfaces.dashboard.settings import get_settings


def main(config):
    # Try loading settings from env vars first
    settings = get_settings()
    config_dict = dict()

    # Load from config if not found in env vars
    if settings.host is None:
        settings.host = config.server.host

    if settings.port is None:
        settings.port = config.server.port

    if settings.project_root is None:
        settings.project_root = config.server.project_root
        config_dict["project_root"] = config.server.project_root

        # Ensure project root exists before starting the server
        if settings.project_root != "" and not os.path.exists(settings.project_root):
            raise ValueError(f"The path `{settings.project_root}` does not exist. "
                             f"Make sure project_root in config is set correctly.")

    print(f"Using settings: {settings}")

    try:
        # Write missing settings to temp env file
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = os.path.join(temp_dir, "cea.env")
            with open(env_file, "w") as f:
                for key, value in config_dict.items():
                    f.write(f"CEA_{key.upper()}={value}\n")
                    f.flush()

            uvicorn.run("cea.interfaces.dashboard.app:app",
                        env_file=env_file,
                        host=settings.host, port=settings.port)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    import cea.config
    main(cea.config.Configuration())
