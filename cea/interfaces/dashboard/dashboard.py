import os
import sys

import uvicorn

from cea.config import Configuration
from cea.interfaces.dashboard.lib.logs import logger
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
        config_project_root = config.server.project_root

        # Treat empty string in config as unset and ignore
        if config_project_root != "":
            settings.project_root = config_project_root

            # Ensure project root exists before starting the server
            if not os.path.exists(settings.project_root):
                raise ValueError(f"The path `{settings.project_root}` does not exist. "
                                f"Make sure project_root in config is set correctly.")


def main(config: Configuration):
    # Load settings from env vars (priority) then config file
    settings = get_settings()
    load_from_config(settings, config)
    logger.info(f"Using settings: {settings}")

    try:
        settings.to_env_vars()

        uvicorn.run("cea.interfaces.dashboard.app:app",
                    reload=config.server.dev,
                    workers=settings.workers,
                    host=settings.host, port=settings.port)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    import cea.config

    main(cea.config.Configuration())
