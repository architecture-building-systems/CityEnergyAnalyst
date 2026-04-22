"""
Entry point for Part 2b (multi-phase). Delegates to the shared
simplified-model runner with ``multi_phase=True``, which requires ≥ 2
network-name entries (one per phase).
"""

import cea.config
from cea.technologies.thermal_network.simplified.main import _run


def main(config: cea.config.Configuration):
    return _run(config, multi_phase=True)


if __name__ == '__main__':
    main(cea.config.Configuration())
