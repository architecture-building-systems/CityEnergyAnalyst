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

    if settings.worker_url is None:
        settings.worker_url = config.worker.url
        config_dict["worker_url"] = config.worker.url

    if settings.project_root is None:
        settings.project_root = config.server.project_root
        config_dict["project_root"] = config.server.project_root

    print(f"Using settings: {settings}")

    try:
        # Write missing settings to temp env file
        with tempfile.NamedTemporaryFile(mode="w") as f:
            for key, value in config_dict.items():
                f.write(f"CEA_{key.upper()}={value}\n")
                f.flush()

            uvicorn.run("cea.interfaces.dashboard.app:app",
                        env_file=f.name,
                        host=settings.host, port=settings.port, reload=True)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    import cea.config
    main(cea.config.Configuration())
