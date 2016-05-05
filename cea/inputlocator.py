"""
inputlocator.py - locate input files by name based on the reference folder structure.
"""
import os
import tempfile


class InputLocator(object):
    """The InputLocator locates files and folders for input to the scripts. This works, because we
    have a convention for the folder structure of a scenario.
    It also provides locations of other files, such as those in the db folder (e.g. archetypes).
    """
    def __init__(self, scenario_path):
        self.scenario_path = scenario_path
        self.db_path = os.path.join(os.path.dirname(__file__), 'db')

    def get_archetypes_hvac_properties(self):
        """/cea/db/Archetypes/Archetypes_HVAC_properties.csv
        path to database of archetypes file Archetypes_HVAC_properties.csv"""
        return os.path.join(self.db_path, 'Archetypes', 'Archetypes_HVAC_properties.csv')

    def get_archetypes_embodied_emissions(self):
        """/cea/db/Archetypes/Archetypes_embodied_emissions.csv
        path to database of archetypes file Archetypes_embodied_emissions.csv"""
        return os.path.join(self.db_path, 'Archetypes', 'Archetypes_embodied_emissions.csv')

    def get_archetypes_embodied_energy(self):
        """/cea/db/Archetypes/Archetypes_embodied_energy.csv
        path to database of archetypes file Archetypes_embodied_energy.csv"""
        return os.path.join(self.db_path, 'Archetypes', 'Archetypes_embodied_energy.csv')

    def get_building_age(self):
        """scenario/1-inputs/1-buildings/building_age.shp"""
        return os.path.join(self.scenario_path, '1-inputs', '1-buildings', 'building_age.shp')

    def get_building_occupancy(self):
        """scenario/1-inputs/1-buildings/building_occupancy.shp"""
        return os.path.join(self.scenario_path, '1-inputs', '1-buildings', 'building_occupancy.shp')

    def get_building_geometry(self):
        """scenario/1-inputs/1-buildings/building_geometry.shp"""
        return os.path.join(self.scenario_path, '1-inputs', '1-buildings', 'building_geometry.shp')

    def get_building_supply(self):
        """scenario/1-inputs/1-buildings/building_supply.shp"""
        return os.path.join(self.scenario_path, '1-inputs', '1-buildings', 'building_supply.shp')

    def get_building_thermal(self):
        """scenario/1-inputs/1-buildings/building_thermal.shp"""
        return os.path.join(self.scenario_path, '1-inputs', '1-buildings', 'building_thermal.shp')

    def get_building_hvac(self):
        """scenario/1-inputs/1-buildings/building_HVAC.shp"""
        return os.path.join(self.scenario_path, '1-inputs', '1-buildings', 'building_HVAC.shp')

    def get_building_architecture(self):
        """scenario/1-inputs/1-buildings/building_architecture.shp"""
        return os.path.join(self.scenario_path, '1-inputs', '1-buildings', 'building_architecture.shp')

    def get_radiation(self):
        """scenario/2-results/1-radiation/1-timeseries/Radiation2000-2010.csv"""
        return os.path.join(self.scenario_path, '2-results', '1-radiation', '1-timeseries', 'radiation.csv')

    def get_weather_hourly(self):
        """scenario/1-inputs/3-weather/weather_hourly.csv"""
        return os.path.join(self.scenario_path, '1-inputs', '3-weather', 'weather_hourly.csv')

    def get_life_cycle_inventory_supply_systems(self):
        """scenario/1-inputs/4-technical/supply_systems.csv"""
        return os.path.join(self.scenario_path, '1-inputs', '4-technical', 'supply_systems.xls')

    def get_technical_emission_systems(self):
        """scenario/1-inputs/4-technical/emission_systems.csv"""
        return os.path.join(self.scenario_path, '1-inputs', '4-technical', 'emission_systems.xls')

    def get_demand_results_folder(self):
        """scenario/2-results/2-demand/1-timeseries"""
        demand_results_folder = os.path.join(self.scenario_path, '2-results', '2-demand', '1-timeseries')
        if not os.path.exists(demand_results_folder):
            os.makedirs(demand_results_folder)
        return demand_results_folder

    def get_demand_results_file(self, building_name):
        """scenario/2-results/2-demand/1-timeseries/{building_name}.csv"""
        demand_results_folder = self.get_demand_results_folder()
        return os.path.join(demand_results_folder, '%s.csv' % building_name)

    def get_demand_plots_folder(self):
        """scenario/2-results/2-demand/2-plots"""
        demand_plots_folder = os.path.join(self.scenario_path, '2-results', '2-demand', '2-plots')
        if not os.path.exists(demand_plots_folder):
            os.makedirs(demand_plots_folder)
        return demand_plots_folder

    def get_demand_plots_file(self, building_name):
        """scenario/2-results/2-demand/2-plots/{building_name}.pdf"""
        demand_plots_folder = self.get_demand_plots_folder()
        return os.path.join(demand_plots_folder, '%s.pdf' % building_name)

    def get_total_demand(self):
        """scenario/2-results/2-demand/1-timeseries/Total_demand.csv"""
        return os.path.join(self.scenario_path, '2-results', '2-demand', '1-timeseries', 'Total_demand.csv')

    def get_lca_emissions_results_folder(self):
        """scenario/2-results/3-emissions/1-timeseries"""
        return os.path.join(self.scenario_path, '2-results', '3-emissions', '1-timeseries')

    def get_heatmaps_demand_folder(self):
        """scenario/2-results/2-demand/3-heatmaps"""
        heatmaps_demand_folder = os.path.join(self.scenario_path, '2-results', '2-demand', '3-heatmaps')
        if not os.path.exists(heatmaps_demand_folder):
            os.makedirs(heatmaps_demand_folder)
        return heatmaps_demand_folder

    def get_heatmaps_emission_folder(self):
        """scenario/2-results/3-emissions/3-heatmaps"""
        return os.path.join(self.scenario_path, '2-results', '3-emissions', '3-heatmaps')

    def get_lca_embodied(self):
        """scenario/2-results/3-emissions/1-timeseries/Total_LCA_embodied.csv"""
        return os.path.join(self.get_lca_emissions_results_folder(), 'Total_LCA_embodied.csv')

    def get_lca_operation(self):
        """scenario/2-results/3-emissions/1-timeseries/Total_LCA_operation.csv"""
        return os.path.join(self.get_lca_emissions_results_folder(), 'Total_LCA_operation.csv')

    def get_schedule(self, schedule):
        """cea/db/Schedules/Occupancy_%SCHEDULE%.csv"""
        return os.path.join(self.db_path, 'Schedules', 'Occupancy_%s.csv' % schedule)

    def get_temporary_folder(self):
        """Temporary folder as returned by `tempfile`."""
        return tempfile.gettempdir()

    def get_temporary_file(self, filename):
        """Returns the path to a file in the temporary folder with the name `filename`"""
        return os.path.join(self.get_temporary_folder(), filename)
