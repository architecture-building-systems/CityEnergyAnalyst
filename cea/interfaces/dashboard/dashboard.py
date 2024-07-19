import sys

import uvicorn

from cea.interfaces.dashboard.settings import get_settings


def main(config):
    # Try loading settings from env vars first
    settings = get_settings()

    # Load from config if not found in env vars
    if settings.host is None:
        settings.host = config.server.host

    if settings.port is None:
        settings.port = config.server.port

    if settings.worker_url is None:
        settings.worker_url = config.worker.url

    print(f"Using settings: {settings}")

    try:
        uvicorn.run("cea.interfaces.dashboard.app:app",
                    host=settings.host, port=settings.port)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    import cea.config
    main(cea.config.Configuration())
