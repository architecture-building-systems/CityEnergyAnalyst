import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:\t  [%(name)s] - %(message)s"
)

logger = logging.getLogger("cea-server")
