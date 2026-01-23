"""Materialise state-in-time scenarios from the district timeline log.

This module exists as a dedicated CEA script entrypoint. The core implementation lives in
`cea.datamanagement.district_level_states.state_scenario`.
"""

from __future__ import annotations

from cea.config import Configuration
from cea.datamanagement.district_level_states.state_scenario import DistrictEventTimeline


def main(config: Configuration) -> None:

    timeline = DistrictEventTimeline(config)
    timeline.bake_states_from_log()
