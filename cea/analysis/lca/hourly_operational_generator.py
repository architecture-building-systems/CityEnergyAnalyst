from cea.config import Configuration
from cea.inputlocator import InputLocator
from cea.analysis.lca.hourly_operational_emission import OperationalHourlyTimeline
from cea.demand.building_properties import BuildingProperties
from cea.datamanagement.database.components import Feedstocks
from cea.utilities import epwreader


def main(config: Configuration) -> None:
    config = Configuration()
    locator = InputLocator(config.scenario)
    buildings = config.hourly_operational_emission.buildings
    weather_path = locator.get_weather_file()
    weather_data = epwreader.epw_reader(weather_path)[
        ["year", "drybulb_C", "wetbulb_C", "relhum_percent", "windspd_ms", "skytemp_C"]
    ]
    building_properties = BuildingProperties(locator, weather_data, buildings)
    feedstock_db = Feedstocks.init_database(locator)
    for building in buildings:
        bpr = building_properties[building]
        timeline = OperationalHourlyTimeline(locator, bpr, feedstock_db)
        timeline.calculate_operational_emission()
        timeline.save_results()


if __name__ == "__main__":
    main(Configuration())