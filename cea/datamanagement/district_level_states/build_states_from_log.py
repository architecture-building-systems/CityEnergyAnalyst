"""Materialise state-in-time scenarios from the district timeline log.

This module exists as a dedicated CEA script entrypoint. The core implementation lives in
`cea.datamanagement.district_level_states.state_scenario`.
"""

from __future__ import annotations

from cea.config import Configuration
from cea.datamanagement.district_level_states.state_scenario import DistrictEventTimeline


def main(config: Configuration) -> None:
    mode = getattr(config.district_events_build, "build_mode")
    regenerate = bool(getattr(config.district_events_build, "regenerate_building_properties"))

    timeline = DistrictEventTimeline(config)
    timeline.build_states_to_file(mode=mode, regenerate_building_properties=regenerate)
