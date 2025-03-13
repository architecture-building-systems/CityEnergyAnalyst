import os
import sys
import tempfile

import uvicorn

from cea.config import Configuration
from cea.interfaces.dashboard.settings import get_settings, Settings


def load_from_config(settings: Settings, config: Configuration) -> None:
    """
    Load settings from config file if not set in Settings (not found in env vars)
    """
    if settings.host is None:
        settings.host = config.server.host

    if settings.port is None:
        settings.port = config.server.port

    if settings.project_root is None:
        settings.project_root = config.server.project_root

        # Ensure project root exists before starting the server
        if settings.project_root != "" and not os.path.exists(settings.project_root):
            raise ValueError(f"The path `{settings.project_root}` does not exist. "
                             f"Make sure project_root in config is set correctly.")


def main(config):
    # Load settings from env vars (priority) then config file
    settings = get_settings()
    load_from_config(settings, config)
    print(f"Using settings: {settings}")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = os.path.join(temp_dir, "cea.env")
            # Rewrite settings to env file to be loaded by uvicorn process
            settings.to_env_file(env_file)

            uvicorn.run("cea.interfaces.dashboard.app:app",
                        reload=config.server.dev,
                        env_file=env_file,
                        host=settings.host, port=settings.port)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    import cea.config

    main(cea.config.Configuration())
