from __future__ import annotations

from cea.config import Configuration
from cea.inputlocator import InputLocator
from cea.demand.building_properties import BuildingProperties
from cea.utilities import epwreader
from cea.datamanagement.database.envelope_lookup import EnvelopeLookup
from cea.analysis.lca.emission_timeline import BuildingEmissionTimeline


def main(config: Configuration) -> None:
    locator = InputLocator(scenario=config.scenario)
    buildings: list[str] = config.emission_timeline.buildings
    end_year: int = config.emission_timeline.end_year

    envelope_lookup = EnvelopeLookup.from_locator(locator)
    weather_path = locator.get_weather_file()
    weather_data = epwreader.epw_reader(weather_path)[
        ["year", "drybulb_C", "wetbulb_C", "relhum_percent", "windspd_ms", "skytemp_C"]
    ]
    building_properties = BuildingProperties(locator, weather_data, buildings)

    for building in buildings:
        timeline = BuildingEmissionTimeline(
            building_properties=building_properties,
            envelope_lookup=envelope_lookup,
            building_name=building,
            locator=locator,
        )
        timeline.generate_timeline(end_year)
        timeline.save_timeline()


if __name__ == "__main__":
    main(Configuration())
