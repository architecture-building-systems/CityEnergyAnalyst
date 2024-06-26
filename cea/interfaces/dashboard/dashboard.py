import sys

import uvicorn


def main(config):
    try:
        uvicorn.run("cea.interfaces.dashboard.app:app", host="127.0.0.1", port=5050)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    import cea.config
    main(cea.config.Configuration())
