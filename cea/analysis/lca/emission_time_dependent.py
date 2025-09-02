from cea.config import Configuration
from cea.inputlocator import InputLocator

from cea.analysis.lca.emission_timeline import BuildingEmissionTimeline
from cea.analysis.lca.hourly_operational_emission import OperationalHourlyTimeline
from cea.demand.building_properties import BuildingProperties
from cea.datamanagement.database.envelope_lookup import EnvelopeLookup
from cea.datamanagement.database.components import Feedstocks
from cea.utilities import epwreader


def operational(config: Configuration) -> None:
    locator = InputLocator(config.scenario)
    buildings = config.emission_time_dependent.buildings
    weather_path = locator.get_weather_file()
    weather_data = epwreader.epw_reader(weather_path)[
        ["year", "drybulb_C", "wetbulb_C", "relhum_percent", "windspd_ms", "skytemp_C"]
    ]
    building_properties = BuildingProperties(locator, weather_data, buildings)
    feedstock_db = Feedstocks.from_locator(locator)
    for building in buildings:
        bpr = building_properties[building]
        timeline = OperationalHourlyTimeline(locator, bpr, feedstock_db)
        timeline.calculate_operational_emission()
        timeline.save_results()
        print(f"Hourly operational emissions for {building} calculated and saved in: {locator.get_lca_operational_hourly_building(building)}.")


def embodied(config: Configuration) -> None:
    locator = InputLocator(scenario=config.scenario)
    buildings: list[str] = config.emission_time_dependent.buildings
    end_year: int = config.emission_time_dependent.end_year

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
        print(f"Embodied and operational emissions timeline for {building} calculated and saved in: {locator.get_lca_timeline_building(building)}.")


def main(config: Configuration) -> None:
    operational(config)
    embodied(config)


if __name__ == "__main__":
    main(Configuration())
