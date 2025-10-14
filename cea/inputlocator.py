"""
inputlocator.py - locate input files by name based on the reference folder structure.
"""
import atexit
import os
import cea.schemas
import shutil
import tempfile

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas", "Jimeno A. Fonseca", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# CEA feature to folder name mapping
CEA_FEATURE_FOLDER_MAP = {
    'sc_ET': 'sc',
    'sc_FP': 'sc',
    'pvt_ET': 'pvt',
    'pvt_FP': 'pvt',
}


class InputLocator(object):
    """The InputLocator locates files and folders for input to the scripts. This works, because we
    have a convention for the folder structure of a scenario.
    It also provides locations of other files, such as those in the databases folder (e.g. archetypes).
    """

    # SCENARIO
    def __init__(self, scenario, plugins=None):
        if not plugins:
            plugins = []
        self.scenario = scenario
        self.db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'databases'))
        self.weather_path = os.path.join(self.db_path, 'weather')
        self._wrap_locator_methods(plugins)
        self.plugins = plugins
        self.optimization_run = None

        self._temp_directory = tempfile.mkdtemp()
        atexit.register(self._cleanup_temp_directory)

    def __getstate__(self):
        """Make sure we can pickle an InputLocator..."""
        return {
            "scenario": self.scenario,
            "db_path": self.db_path,
            "weather_path": self.weather_path,
            "plugins": [str(p) for p in self.plugins],
            "_temp_directory": self._temp_directory
        }

    def __setstate__(self, state):
        from cea.plugin import instantiate_plugin

        self.scenario = state["scenario"]
        self.db_path = state["db_path"]
        self.weather_path = state["weather_path"]
        self.plugins = [instantiate_plugin(plugin_fqname) for plugin_fqname in state["plugins"]]
        self._wrap_locator_methods(self.plugins)
        self._temp_directory = state["_temp_directory"]

    def _cleanup_temp_directory(self):
        # Cleanup the temporary directory when the object is destroyed
        if os.path.exists(self._temp_directory):
            shutil.rmtree(self._temp_directory)

    def _wrap_locator_methods(self, plugins):
        """
        For each locator method defined in schemas.yml, wrap it in a callable object (preserving the
        original interface) that allows for read() and write() operations.
        """
        schemas = cea.schemas.schemas(plugins)
        for lm in schemas.keys():
            if hasattr(self, lm):
                # allow cea.inputlocator.InputLocator to define locator methods
                setattr(self, lm, cea.schemas.create_schema_io(self, lm, schemas[lm], getattr(self.__class__, lm)))
            else:
                # create locator methods based on schemas if not overridden in InputLocator
                setattr(self, lm, cea.schemas.create_schema_io(self, lm, schemas[lm]))

    @staticmethod
    def _ensure_folder(*components) -> str:
        """Return the `*components` joined together as a path to a folder and ensure that that folder exists on disc.
        If it doesn't exist yet, attempt to make it with `os.makedirs`."""
        folder = os.path.join(*components)
        os.makedirs(folder, exist_ok=True)

        return folder

    @staticmethod
    def _clear_folder(folder):
        """Delete all files in a folder"""
        if not os.path.exists(folder):
            return

        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))

    def ensure_parent_folder_exists(self, file_path):
        """Use os.makedirs to ensure the folders exist"""
        self._ensure_folder(os.path.dirname(file_path))

    # Paths to databases
    def get_databases_folder(self):
        """Returns the inputs folder of a scenario"""
        return os.path.join(self.get_input_folder(), "technology")

    def get_databases_archetypes_folder(self):
        return os.path.join(self.get_databases_folder(), 'archetypes')

    def get_databases_assemblies_folder(self):
        return os.path.join(self.get_databases_folder(), 'assemblies')

    def get_databases_systems_folder(self):
        return os.path.join(self.get_databases_folder(), 'components')

    def get_database_use_types_folder(self):
        return os.path.join(self.get_databases_archetypes_folder(), 'use_types')

    def get_database_standard_schedules_use(self, use):
        return os.path.join(self.get_database_use_types_folder(), use + '.csv')

    def get_input_folder(self):
        """Returns the inputs folder of a scenario"""
        return os.path.join(self.scenario, "inputs")

    def get_export_folder(self):
        """Returns the export folder of a scenario"""
        return os.path.join(self.scenario, "export")

    def get_export_results_folder(self):
        """Returns the folder storing the summary and analytics results in the export folder of a scenario"""
        """scenario/export/results"""
        return os.path.join(self.get_export_folder(), "results")

    def get_export_plots_folder(self):
        """Returns the folder storing the plots in the export folder of a scenario"""
        """scenario/export/plots"""
        return os.path.join(self.get_export_folder(), "plots")

    def get_export_plots_cea_feature_folder(self, plot_cea_feature):
        """Returns the folder storing the plots in the export folder of a scenario"""
        """scenario/export/plots/{plot_cea_feature}"""
        return os.path.join(self.get_export_plots_folder(), plot_cea_feature)

    def get_export_plots_selected_building_file(self):
        """scenario/export/plots/{plot_cea_feature}/selected_buildings.csv"""
        return os.path.join(self.get_export_plots_folder(), 'selected_buildings.csv')

    def get_export_results_summary_folder(self, folder_name):
        """scenario/export/results/{folder_name}"""
        return os.path.join(self.get_export_results_folder(), folder_name)

    def get_export_results_summary_selected_building_file(self, summary_folder):
        """scenario/export/results/{folder_name}/selected_buildings.csv"""
        return os.path.join(summary_folder, '_selected_buildings.csv')

    def get_export_results_summary_cea_feature_time_period_file(self, summary_folder, cea_feature: str, appendix,
                                                                time_period, hour_start, hour_end):
        """scenario/export/results/{folder_name}/{cea_feature}/{appendix}_{time_period}.csv"""
        folder_name = CEA_FEATURE_FOLDER_MAP.get(cea_feature, cea_feature)
        if abs(hour_end - hour_start) != 8760 and time_period == 'annually':
            return os.path.join(summary_folder, folder_name, f'{appendix}_selected_hours.csv')
        else:
            return os.path.join(summary_folder, folder_name, f'{appendix}_{time_period}.csv')

    def get_export_results_summary_cea_feature_buildings_file(self, summary_folder, cea_feature: str, appendix):
        """scenario/export/results/{folder_name}/{cea_feature}/{appendix}_buildings.csv"""
        folder_name = CEA_FEATURE_FOLDER_MAP.get(cea_feature, cea_feature)
        return os.path.join(summary_folder, folder_name, f"{appendix}_buildings.csv")

    def get_export_results_summary_cea_feature_timeline_file(self, summary_folder, cea_feature: str, appendix):
        """scenario/export/results/{folder_name}/{cea_feature}/{appendix}_timeline.csv"""
        folder_name = CEA_FEATURE_FOLDER_MAP.get(cea_feature, cea_feature)
        return os.path.join(summary_folder, folder_name, f"{appendix}_timeline.csv")

    def get_export_plots_cea_feature_buildings_file(self, plot_cea_feature, appendix):
        """scenario/export/plots/{plot_cea_feature}/{appendix}_buildings.csv"""
        return os.path.join(self.get_export_plots_cea_feature_folder(plot_cea_feature),
                            f"{appendix}_buildings.csv")

    def get_export_results_summary_cea_feature_time_resolution_buildings_file(self, summary_folder, cea_feature: str,
                                                                              appendix, time_period, hour_start,
                                                                              hour_end):
        """scenario/export/results/{folder_name}/{cea_feature}/{appendix}_{time_resolution}_buildings.csv"""
        folder_name = CEA_FEATURE_FOLDER_MAP.get(cea_feature, cea_feature)
        if abs(hour_end - hour_start) != 8760 and time_period == 'annually':
            return os.path.join(summary_folder, folder_name, f'{appendix}_selected_hours_buildings.csv')
        else:
            return os.path.join(summary_folder, folder_name, f"{appendix}_{time_period}_buildings.csv")

    def get_export_plots_cea_feature_time_resolution_buildings_file(self, plot_cea_feature, appendix,
                                                                      time_period, hour_start, hour_end):
        """scenario/export/plots/{plot_cea_feature}/{appendix}_{time_resolution}_buildings.csv"""
        if plot_cea_feature == 'lifecycle-emissions':
            return os.path.join(self.get_export_plots_cea_feature_folder(plot_cea_feature),
                                f"{appendix}_buildings.csv")
        elif abs(hour_end - hour_start) != 8760 and time_period == 'annually':
            return os.path.join(self.get_export_plots_cea_feature_folder(plot_cea_feature),
                                f'{appendix}_selected_hours_buildings.csv')
        else:
            return os.path.join(self.get_export_plots_cea_feature_folder(plot_cea_feature),
                                f"{appendix}_{time_period}_buildings.csv")

    def get_export_results_summary_cea_feature_analytics_folder(self, summary_folder, cea_feature: str):
        """scenario/export/results/{folder_name}/{cea_feature}/analytics"""
        return os.path.join(summary_folder, CEA_FEATURE_FOLDER_MAP.get(cea_feature, cea_feature), 'analytics')

    def get_export_results_summary_cea_feature_analytics_time_resolution_file(self, summary_folder, cea_feature,
                                                                              appendix, time_period, hour_start,
                                                                              hour_end):
        """scenario/export/results/{folder_name}/{cea_feature}/analytics/{appendix}_analytics_{time_period}.csv"""
        if abs(hour_end - hour_start) != 8760 and time_period == 'annually':
            return os.path.join(
                self.get_export_results_summary_cea_feature_analytics_folder(summary_folder, cea_feature),
                f'{appendix}_analytics_selected_hours.csv')
        else:
            return os.path.join(
                self.get_export_results_summary_cea_feature_analytics_folder(summary_folder, cea_feature),
                f'{appendix}_analytics_{time_period}.csv')

    def get_export_results_summary_cea_feature_analytics_time_resolution_buildings_file(self, summary_folder,
                                                                                        cea_feature, appendix,
                                                                                        time_period, hour_start,
                                                                                        hour_end):
        """scenario/export/results/{folder_name}/{cea_feature}/analytics/{appendix}_analytics_{time_resolution}_buildings.csv"""
        if abs(hour_end - hour_start) != 8760 and time_period == 'annually':
            return os.path.join(
                self.get_export_results_summary_cea_feature_analytics_folder(summary_folder, cea_feature),
                f"{appendix}_analytics_selected_hours_buildings.csv")
        else:
            return os.path.join(
                self.get_export_results_summary_cea_feature_analytics_folder(summary_folder, cea_feature),
                f"{appendix}_analytics_{time_period}_buildings.csv")

    def get_export_plots_cea_feature_analytics_folder(self, plot_cea_feature):
        """scenario/export/plots/{plot_cea_feature}/analytics"""
        return os.path.join(self.get_export_plots_cea_feature_folder(plot_cea_feature), 'analytics')

    def get_export_plots_cea_feature_analytics_time_resolution_buildings_file(self, plot_cea_feature,
                                                                              appendix, time_period, hour_start,
                                                                              hour_end):
        """scenario/export/plots/{plot_cea_feature}/{cea_feature}/analytics/{appendix}_analytics_{time_resolution}_buildings.csv"""
        if abs(hour_end - hour_start) != 8760 and time_period == 'annually':
            return os.path.join(
                self.get_export_plots_cea_feature_analytics_folder(plot_cea_feature),
                f"{appendix}_analytics_selected_hours_buildings.csv")
        else:
            return os.path.join(
                self.get_export_plots_cea_feature_analytics_folder(plot_cea_feature),
                f"{appendix}_analytics_{time_period}_buildings.csv")

    def get_export_to_rhino_from_cea_folder(self):
        """scenario/export/rhino/from_cea"""
        return os.path.join(self.get_export_folder(), 'rhino', 'from_cea')

    def get_export_to_rhino_from_cea_zone_to_csv(self):
        """scenario/export/rhino/from_cea/zone_to.csv"""
        return os.path.join(self.get_export_to_rhino_from_cea_folder(), 'zone_out.csv')

    def get_export_to_rhino_from_cea_site_to_csv(self):
        """scenario/export/rhino/from_cea/site_to.csv"""
        return os.path.join(self.get_export_to_rhino_from_cea_folder(), 'site_out.csv')

    def get_export_to_rhino_from_cea_surroundings_to_csv(self):
        """scenario/export/rhino/from_cea/surroundings_to.csv"""
        return os.path.join(self.get_export_to_rhino_from_cea_folder(), 'surroundings_out.csv')

    def get_export_to_rhino_from_cea_streets_to_csv(self):
        """scenario/export/rhino/from_cea/streets_to.csv"""
        return os.path.join(self.get_export_to_rhino_from_cea_folder(), 'streets_out.csv')

    def get_export_to_rhino_from_cea_trees_to_csv(self):
        """scenario/export/rhino/from_cea/trees_to.csv"""
        return os.path.join(self.get_export_to_rhino_from_cea_folder(), 'trees_out.csv')

    def get_export_to_rhino_from_cea_district_heating_network_edges_to_csv(self):
        """scenario/export/rhino/from_cea/dh_edges_out.csv"""
        return os.path.join(self.get_export_to_rhino_from_cea_folder(), 'dh_edges_out.csv')

    def get_export_to_rhino_from_cea_district_cooling_network_edges_to_csv(self):
        """scenario/export/rhino/from_cea/dc_edges_out.csv"""
        return os.path.join(self.get_export_to_rhino_from_cea_folder(), 'dc_edges_out.csv')

    def get_export_to_rhino_from_cea_district_heating_network_nodes_to_csv(self):
        """scenario/export/rhino/from_cea/dh_nodes_out.csv"""
        return os.path.join(self.get_export_to_rhino_from_cea_folder(), 'dh_nodes_out.csv')

    def get_export_to_rhino_from_cea_district_cooling_network_nodes_to_csv(self):
        """scenario/export/rhino/from_cea/dc_nodes_out.csv"""
        return os.path.join(self.get_export_to_rhino_from_cea_folder(), 'dc_nodes_out.csv')

    def get_optimization_results_folder(self):
        """Returns the folder containing the scenario's optimization results"""
        return os.path.join(self.scenario, 'outputs', 'data', 'optimization')


    def get_electrical_and_thermal_network_optimization_results_folder(self):
        """scenario/outputs/data/optimization"""
        return os.path.join(self.get_optimization_results_folder(), 'electrical_and_thermal_network')

    def get_optimization_master_results_folder(self):
        """Returns the folder containing the scenario's optimization Master Checkpoints"""
        return os.path.join(self.get_optimization_results_folder(), "master")

    def get_optimization_slave_results_folder(self):
        """Returns the folder containing the scenario's optimization Slave results (storage + operation pattern)"""
        return os.path.join(self.get_optimization_results_folder(), "slave")

    def get_optimization_slave_generation_results_folder(self, gen_num):
        """Returns the folder containing the scenario's optimization Slave results (storage + operation pattern)"""
        return os.path.join(
            os.path.join(self.get_optimization_slave_results_folder(), "gen_%(gen_num)s" % locals()))

    def get_optimization_individuals_in_generation(self, gen_num):
        """scenario/outputs/data/optimization/slave/gen_[gen_num]/..."""
        return os.path.join(self.get_optimization_slave_generation_results_folder(gen_num),
                            'generation_%(gen_num)s_individuals.csv' % locals())

    def get_optimization_slave_heating_activation_pattern(self, ind_num, gen_num):
        """scenario/outputs/data/optimization/slave/gen_[gen_num]/..."""
        return os.path.join(self.get_optimization_slave_generation_results_folder(gen_num),
                            'ind_%(ind_num)s_Heating_Activation_Pattern.csv' % locals())

    def get_optimization_slave_cooling_activation_pattern(self, ind_num, gen_num):
        """scenario/outputs/data/optimization/slave/gen_[gen_num]/..."""
        return os.path.join(self.get_optimization_slave_generation_results_folder(gen_num),
                            'ind_%(ind_num)s_Cooling_Activation_Pattern.csv' % locals())

    def get_optimization_slave_electricity_requirements_data(self, ind_num, gen_num):
        """scenario/outputs/data/optimization/slave/gen_[gen_num]/..."""
        return os.path.join(self.get_optimization_slave_generation_results_folder(gen_num),
                            'ind_%(ind_num)s_Electricity_Requirements_Pattern.csv' % locals())

    def get_optimization_slave_electricity_activation_pattern(self, ind_num, gen_num):
        """scenario/outputs/data/optimization/slave/gen_[gen_num]/..."""
        return os.path.join(self.get_optimization_slave_generation_results_folder(gen_num),
                            'ind_%(ind_num)s_Electricity_Activation_Pattern.csv' % locals())

    def get_optimization_district_scale_heating_capacity(self, ind_num, gen_num):
        """scenario/outputs/data/optimization/slave/gen_[gen_num]/..."""
        return os.path.join(self.get_optimization_slave_generation_results_folder(gen_num),
                            'ind_%(ind_num)s_district_scale_heating_capacity.csv' % locals())

    def get_optimization_district_scale_cooling_capacity(self, ind_num, gen_num):
        """scenario/outputs/data/optimization/slave/gen_[gen_num]/..."""
        return os.path.join(self.get_optimization_slave_generation_results_folder(gen_num),
                            'ind_%(ind_num)s_district_scale_cooling_capacity.csv' % locals())

    def get_optimization_district_scale_electricity_capacity(self, ind_num, gen_num):
        """scenario/outputs/data/optimization/slave/gen_[gen_num]/..."""
        return os.path.join(self.get_optimization_slave_generation_results_folder(gen_num),
                            'ind_%(ind_num)s_district_scale_electrical_capacity.csv' % locals())

    def get_optimization_building_scale_heating_capacity(self, ind_num, gen_num):
        """scenario/outputs/data/optimization/slave/gen_[gen_num]/..."""
        return os.path.join(self.get_optimization_slave_generation_results_folder(gen_num),
                            'ind_%(ind_num)s_building_scale_heating_capacity.csv' % locals())

    def get_optimization_building_scale_cooling_capacity(self, ind_num, gen_num):
        """scenario/outputs/data/optimization/slave/gen_[gen_num]/..."""
        return os.path.join(self.get_optimization_slave_generation_results_folder(gen_num),
                            'ind_%(ind_num)s_building_scale_cooling_capacity.csv' % locals())

    def get_optimization_slave_district_scale_performance(self, ind_num, gen_num):
        """scenario/outputs/data/optimization/slave/gen_[gen_num]/..."""
        return os.path.join(self.get_optimization_slave_generation_results_folder(gen_num),
                            'ind_%(ind_num)s_buildings_district_scale_performance.csv' % locals())

    def get_optimization_slave_building_scale_performance(self, ind_num, gen_num):
        """scenario/outputs/data/optimization/slave/gen_[gen_num]/..."""
        return os.path.join(self.get_optimization_slave_generation_results_folder(gen_num),
                            'ind_%(ind_num)s_buildings_building_scale_performance.csv' % locals())

    def get_optimization_slave_building_connectivity(self, ind_num, gen_num):
        """scenario/outputs/data/optimization/slave/gen_[gen_num]/..."""
        return os.path.join(self.get_optimization_slave_generation_results_folder(gen_num),
                            'ind_%(ind_num)s_building_connectivity.csv' % locals())

    def get_optimization_slave_total_performance(self, ind_num, gen_num):
        """scenario/outputs/data/optimization/slave/gen_[gen_num]/..."""
        return os.path.join(self.get_optimization_slave_generation_results_folder(gen_num),
                            'ind_%(ind_num)s_total_performance.csv' % locals())

    def get_optimization_generation_district_scale_performance(self, gen_num):
        """scenario/outputs/data/optimization/slave/gen_[gen_num]/..."""
        return os.path.join(self.get_optimization_slave_generation_results_folder(gen_num),
                            'gen_%(gen_num)s_district_scale_performance.csv' % locals())

    def get_optimization_generation_building_scale_performance(self, gen_num):
        """scenario/outputs/data/optimization/slave/gen_[gen_num]/..."""
        return os.path.join(self.get_optimization_slave_generation_results_folder(gen_num),
                            'gen_%(gen_num)s_building_scale_performance.csv' % locals())

    def get_optimization_generation_total_performance(self, gen_num):
        """scenario/outputs/data/optimization/slave/gen_[gen_num]/..."""
        return os.path.join(self.get_optimization_slave_generation_results_folder(gen_num),
                            'gen_%(gen_num)s_total_performance.csv' % locals())

    def get_optimization_generation_total_performance_pareto(self, gen_num):
        """scenario/outputs/data/optimization/slave/gen_[gen_num]/..."""
        return os.path.join(self.get_optimization_slave_generation_results_folder(gen_num),
                            'gen_%(gen_num)s_total_performance_pareto.csv' % locals())

    def get_optimization_decentralized_folder_building_result_cooling(self, building, configuration='AHU_ARU_SCU'):
        """scenario/outputs/data/optimization/decentralized/..."""
        return os.path.join(self.get_optimization_decentralized_folder(),
                            building + '_' + configuration + '_result_cooling.csv')

    def get_optimization_decentralized_folder_building_result_cooling_activation(self, building,
                                                                                 configuration='AHU_ARU_SCU'):
        """scenario/outputs/data/optimization/decentralized/..."""

        return os.path.join(self.get_optimization_decentralized_folder(),
                            building + '_' + configuration + '_cooling_activation.csv')

    def get_optimization_decentralized_folder_building_result_heating(self, building):
        """scenario/outputs/data/optimization/decentralized/..."""
        return os.path.join(self.get_optimization_decentralized_folder(),
                            'DiscOp_' + building + '_result_heating.csv')

    def get_optimization_decentralized_folder_building_result_heating_activation(self, building):
        """scenario/outputs/data/optimization/decentralized/..."""
        return os.path.join(self.get_optimization_decentralized_folder(),
                            'DiscOp_' + building + '_result_heating_activation.csv')

    def get_optimization_network_results_summary(self, network_type, district_network_barcode):
        """scenario/outputs/data/optimization/network/..."""
        district_network_barcode_hex = hex(int(str(district_network_barcode), 2))
        path = os.path.join(self.get_optimization_network_results_folder(),
                            network_type + '_' + 'Network_summary_result_' + district_network_barcode_hex + '.csv')
        return path

    def get_optimization_network_results_folder(self):
        """scenario/outputs/data/optimization/network
        Network summary results
        """
        return os.path.join(self.get_optimization_results_folder(), "network")

    def get_optimization_network_layout_folder(self):
        """scenario/outputs/data/optimization/network/layout
        Network layout files
        """
        return os.path.join(self.get_optimization_network_results_folder(), "layout")

    def get_optimization_network_layout_costs_file(self, network_type):
        """scenario/outputs/data/optimization/network/layout/DC_costs.csv
        Optimized network layout files for pipes of district heating networks
        """
        return os.path.join(self.get_optimization_network_layout_folder(),
                            str(network_type) + "_costs.csv")

    def get_optimization_network_individual_results_file(self, network_type, individual):
        """scenario/outputs/data/optimization/network/layout/DH_T_Return.csv or DC_T_Return.csv
        Folder to results file of this generation
        """
        return os.path.join(self.get_optimization_network_results_folder(),
                            network_type + "_" + str(individual) + ".csv")

    def get_optimization_network_generation_individuals_results_file(self, network_type, generation):
        """scenario/outputs/data/optimization/network/layout/DH_T_Return.csv or DC_T_Return.csv
        Folder to results file of this generation
        """
        return os.path.join(self.get_optimization_network_results_folder(),
                            network_type + '_' + str(generation) + "_individuals.csv")

    def get_optimization_network_all_individuals_results_file(self, network_type):
        """scenario/outputs/data/optimization/network/layout/DH_T_Return.csv or DC_T_Return.csv
        Folder to results file of this generation
        """
        return os.path.join(self.get_optimization_network_results_folder(),
                            network_type + "_all_individuals.csv")

    def get_optimization_decentralized_folder(self):
        """scenario/outputs/data/optimization/decentralized
        Operation pattern for decentralized buildings"""
        return os.path.join(self.get_optimization_results_folder(), "decentralized")

    def get_optimization_checkpoint(self, generation):
        """scenario/outputs/data/optimization/master/..."""
        return os.path.join(self.get_optimization_master_results_folder(),
                            'CheckPoint_' + str(generation) + ".json")

    def get_optimization_substations_folder(self):
        """scenario/outputs/data/optimization/substations
        Substation results for decentralized buildings"""
        return os.path.join(self.get_optimization_results_folder(), "decentralized", "substations")

    def get_optimization_substations_results_file(self, building, network_type, district_network_barcode):
        """scenario/outputs/data/optimization/substations/${building}_result.csv"""
        if district_network_barcode == "":
            district_network_barcode = "0"
        district_network_barcode_hex = hex(int(str(district_network_barcode), 2))
        return os.path.join(self.get_optimization_substations_folder(),
                            "%(district_network_barcode_hex)s%(network_type)s_%(building)s_result.csv" % locals())

    def get_optimization_substations_total_file(self, district_network_barcode, network_type):
        """scenario/outputs/data/optimization/substations/Total_${genome}.csv"""
        if district_network_barcode == "":
            district_network_barcode = "0"
        district_network_barcode_hex = hex(int(str(district_network_barcode), 2))
        return os.path.join(self.get_optimization_substations_folder(),
                            "Total_%(network_type)s_%(district_network_barcode_hex)s.csv" % locals())

    # OPTIMIZATION *NEW*
    def get_centralized_optimization_results_folder(self):
        """Returns the folder containing the scenario's results for the new optimization script"""
        if self.optimization_run:
            return os.path.join(self.get_optimization_results_folder(), f'centralized_run_{self.optimization_run}')
        else:
            return os.path.join(self.get_optimization_results_folder(), 'centralized')

    def register_centralized_optimization_run_id(self):
        """Registers the run_id of the centralized optimization run"""
        i = 1
        while True:
            results_folder = os.path.join(self.get_optimization_results_folder(), f'centralized_run_{i}')
            if not os.path.exists(results_folder):
                self.optimization_run = i
                break
            i += 1

    def clear_centralized_optimization_results_folder(self):
        """Deletes the folder containing the scenario's results for the new optimization script"""
        return self._clear_folder(self.get_centralized_optimization_results_folder())

    def get_new_optimization_des_solution_folders(self):
        """Returns the folder structure of the optimization results folder"""
        des_solution_folders = next(os.walk(self.get_centralized_optimization_results_folder()))[1]
        des_solution_folders = [folder for folder in des_solution_folders if folder != 'debugging']
        return des_solution_folders

    def get_new_optimization_base_case_folder(self, network_type):
        """Returns the folder containing the base-case energy systems against which optimal systems are compared"""
        return os.path.join(self.get_centralized_optimization_results_folder(), f'base_{network_type}S')

    def get_new_optimization_optimal_district_energy_system_folder(self,
                                                                   district_energy_system_id='current_DES'):
        """Returns the results-folder for the n-th near pareto-optimal district energy system"""
        return os.path.join(self.get_centralized_optimization_results_folder(),
                                   f'{district_energy_system_id}')

    def get_new_optimization_optimal_networks_folder(self, district_energy_system_id='current_DES'):
        """Returns the results-folder for the i-th network of the n-th near-pareto-optimal DES"""
        des_folder = self.get_new_optimization_optimal_district_energy_system_folder(district_energy_system_id)
        return os.path.join(des_folder, 'networks')

    def get_new_optimization_optimal_network_layout_file(self, district_energy_system_id='current_DES',
                                                         network_id='N0000'):
        """Returns the result-path for the layout of the i-th network of the n-th near-pareto-optimal DES"""
        network_folder = self.get_new_optimization_optimal_networks_folder(district_energy_system_id)
        return os.path.join(network_folder, f'{network_id}_layout.geojson')

    def get_new_optimization_optimal_supply_systems_folder(self, district_energy_system_id='current_DES'):
        """Returns the results-file for the general supply systems results of the n-th near-pareto-optimal DES"""
        des_folder = self.get_new_optimization_optimal_district_energy_system_folder(district_energy_system_id)
        return os.path.join(des_folder, 'Supply_systems')

    def get_new_optimization_optimal_supply_system_ids(self, district_energy_system_id='current_DES'):
        """Returns the identifiers of the supply systems of the n-th near-pareto-optimal DES"""
        des_supsys_folder = self.get_new_optimization_optimal_supply_systems_folder(district_energy_system_id)
        supply_system_files = next(os.walk(des_supsys_folder))[2]
        supply_system_ids = [file.split('_')[0] for file in supply_system_files
                             if file.split('.')[1] == 'csv' and file.split('_')[0] != 'Supply']
        return supply_system_ids

    def get_new_optimization_optimal_supply_system_file(self, district_energy_system_id='current_DES',
                                                        supply_system_id='N0000_or_B0000'):
        """Returns the results-file for the supply systems summary of the n-th near-pareto-optimal DES"""
        des_supsys_folder = self.get_new_optimization_optimal_supply_systems_folder(district_energy_system_id)
        return os.path.join(des_supsys_folder, f'{supply_system_id}_supply_system_structure.csv')

    def get_new_optimization_optimal_supply_systems_summary_file(self, district_energy_system_id='current_DES'):
        """Returns the results-file for the supply systems summary of the n-th near-pareto-optimal DES"""
        des_supsys_folder = self.get_new_optimization_optimal_supply_systems_folder(district_energy_system_id)
        return os.path.join(des_supsys_folder, 'Supply_systems_summary.csv')

    def get_new_optimization_supply_system_details_folder(self, district_energy_system_id='current_DES'):
        """Returns the results-folder for the detailed supply system information of the n-th near-pareto-optimal DES"""
        des_folder = self.get_new_optimization_optimal_district_energy_system_folder(district_energy_system_id)
        return os.path.join(des_folder, 'Supply_system_operation_details')

    def get_new_optimization_detailed_network_performance_file(self, district_energy_system_id='current_DES'):
        """Returns the results-file for the detailed performance of the n-th near-pareto-optimal DES's networks"""
        des_details_folder = self.get_new_optimization_supply_system_details_folder(district_energy_system_id)
        return os.path.join(des_details_folder, 'network_performance.csv')

    def get_new_optimization_supply_systems_detailed_operation_file(self,
                                                                    district_energy_system_id='current_DES',
                                                                    supply_system_id='N0000_or_B0000'):
        """Returns the results-file for the supply systems operation profiles of the n-th near-pareto-optimal DES"""
        des_details_folder = self.get_new_optimization_supply_system_details_folder(district_energy_system_id)
        return os.path.join(des_details_folder, f'{supply_system_id}_operation.csv')

    def get_new_optimization_supply_systems_annual_breakdown_file(self, district_energy_system_id='current_DES',
                                                                  supply_system_id='N0000_or_B0000'):
        """Returns the results-file for the breakdown of a supply systems annual operation (in terms of energy demand,
        cost, GHG- and heat-emissions) in the n-th near-pareto-optimal DES"""
        des_details_folder = self.get_new_optimization_supply_system_details_folder(district_energy_system_id)
        return os.path.join(des_details_folder, f'{supply_system_id}_annual_breakdown.csv')

    def get_new_optimization_debugging_folder(self):
        """Returns the debugging-folder, used to store information gathered by the optimisation tracker"""
        return os.path.join(self.get_centralized_optimization_results_folder(), 'debugging')

    def get_new_optimization_debugging_network_tracker_file(self):
        """Returns the debugging-file, used to store information gathered by the optimisation tracker"""
        return os.path.join(self.get_new_optimization_debugging_folder(), 'network_tracker.csv')

    def get_new_optimization_debugging_supply_system_tracker_file(self):
        """Returns the debugging-file, used to store information gathered by the optimisation tracker"""
        return os.path.join(self.get_new_optimization_debugging_folder(), 'supply_system_tracker.csv')

    def get_new_optimization_debugging_fitness_tracker_file(self):
        """Returns the debugging-file, used to store information gathered by the optimisation tracker"""
        return os.path.join(self.get_new_optimization_debugging_folder(), 'fitness_tracker.csv')

    # POTENTIAL
    def get_potentials_folder(self):
        """scenario/outputs/data/potentials"""
        return os.path.join(self.scenario, 'outputs', 'data', 'potentials')

    def get_sewage_heat_potential(self):
        return os.path.join(self.get_potentials_folder(), "Sewage_heat_potential.csv")

    def get_water_body_potential(self):
        return os.path.join(self.get_potentials_folder(), "Water_body_potential.csv")

    def get_geothermal_potential(self):
        """scenario/outputs/data/potentials/geothermal/Shallow_geothermal_potential.csv"""
        return os.path.join(self.get_potentials_folder(), "Shallow_geothermal_potential.csv")

    def get_weather_file(self):
        """inputs/weather/weather.epw
        path to the weather file to use for simulation - run weather-helper to set this"""
        return os.path.join(self.get_weather_folder(), "weather.epw")

    def get_weather(self, name=None):
        """weather/{name}.epw Returns the path to a weather file with the name ``name``. This can either be one
        of the pre-configured weather files (see ``get_weather_names``) or a path to an existing weather file.
        Returns the default weather file if no other file can be resolved.
        ..note: scripts should not use this, instead, use ``get_weather_file()`` - see the ``weather-helper`` script."""
        default_weather_name = self.get_weather_names()[0]
        if not name:
            name = default_weather_name
        if os.path.exists(name) and name.endswith('.epw'):
            return name

        if name not in self.get_weather_names():
            # allow using an abbreviation like "Zug" for "Zug-inducity_1990_2010_TMY"
            for n in self.get_weather_names():
                if n.lower().startswith(name.lower()):
                    name = n
                    break
        weather_file = os.path.join(self.weather_path, name + '.epw')
        if not os.path.exists(weather_file):
            return os.path.join(self.weather_path, default_weather_name + '.epw')
        return weather_file

    def get_weather_names(self):
        """Return a list of all installed epw files in the system"""
        weather_names = [os.path.splitext(f)[0] for f in os.listdir(self.weather_path) if f.endswith('.epw')]
        return weather_names

    def get_weather_folder(self):
        return os.path.join(self.get_input_folder(), 'weather')

    def get_db4_folder(self):
        """scenario/inputs/database/"""
        return os.path.join(self.scenario, 'inputs', 'database')

    def get_db4_archetypes_folder(self):
        """scenario/inputs/database/ARCHETYPES"""
        return os.path.join(self.get_db4_folder(), 'ARCHETYPES')

    def get_db4_archetypes_construction_folder(self):
        """scenario/inputs/database/ARCHETYPES/CONSTRUCTION"""
        return os.path.join(self.get_db4_archetypes_folder(), 'CONSTRUCTION')

    def get_database_archetypes_construction_type(self):
        """scenario/inputs/database/ARCHETYPES/CONSTRUCTION/CONSTRUCTION_TYPES.csv"""
        return os.path.join(self.get_db4_archetypes_construction_folder(), 'CONSTRUCTION_TYPES.csv')

    def get_db4_archetypes_use_folder(self):
        """scenario/inputs/database/ARCHETYPES/USE"""
        return os.path.join(self.get_db4_archetypes_folder(), 'USE')

    def get_database_archetypes_use_type(self):
        """scenario/inputs/database/ARCHETYPES/USE/USE_TYPES.csv"""
        return os.path.join(self.get_db4_archetypes_use_folder(), 'USE_TYPES.csv')

    def get_db4_archetypes_schedules_folder(self):
        """scenario/inputs/database/ARCHETYPES/USE/SCHEDULES"""
        return os.path.join(self.get_db4_archetypes_use_folder(), 'SCHEDULES')

    def get_db4_archetypes_schedules_library_folder(self):
        """scenario/inputs/database/ARCHETYPES/USE/SCHEDULES/SCHEDULES_LIBRARY"""
        return os.path.join(self.get_db4_archetypes_use_folder(), 'SCHEDULES', 'SCHEDULES_LIBRARY')

    def get_database_archetypes_schedules(self, use_type):
        """scenario/inputs/database/ARCHETYPES/USE/SCHEDULES/SCHEDULES_LIBRARY/{use}.csv"""
        return os.path.join(self.get_db4_archetypes_schedules_library_folder(), f'{use_type}.csv')

    def get_database_archetypes_schedules_monthly_multiplier(self):
        """scenario/inputs/database/ARCHETYPES/USE/SCHEDULES/MONTHLY_MULTIPLIERS.csv"""
        return os.path.join(self.get_db4_archetypes_schedules_folder(), 'MONTHLY_MULTIPLIERS.csv')

    def get_db4_assemblies_folder(self):
        """scenario/inputs/database/ASSEMBLIES"""
        return os.path.join(self.get_db4_folder(), 'ASSEMBLIES')

    def get_db4_assemblies_envelope_folder(self):
        """scenario/inputs/database/ASSEMBLIES/ENVELOPE"""
        return os.path.join(self.get_db4_assemblies_folder(), 'ENVELOPE')

    def get_database_assemblies_envelope_floor(self):
        """scenario/inputs/database/ASSEMBLIES/ENVELOPE/ENVELOPE_FLOOR.csv"""
        return os.path.join(self.get_db4_assemblies_envelope_folder(), 'ENVELOPE_FLOOR.csv')

    def get_database_assemblies_envelope_window(self):
        """scenario/inputs/database/ASSEMBLIES/ENVELOPE/ENVELOPE_WINDOW.csv"""
        return os.path.join(self.get_db4_assemblies_envelope_folder(), 'ENVELOPE_WINDOW.csv')

    def get_database_assemblies_envelope_mass(self):
        """scenario/inputs/database/ASSEMBLIES/ENVELOPE/ENVELOPE_MASS.csv"""
        return os.path.join(self.get_db4_assemblies_envelope_folder(), 'ENVELOPE_MASS.csv')

    def get_database_assemblies_envelope_tightness(self):
        """scenario/inputs/database/ASSEMBLIES/ENVELOPE/ENVELOPE_TIGHTNESS.csv"""
        return os.path.join(self.get_db4_assemblies_envelope_folder(), 'ENVELOPE_TIGHTNESS.csv')

    def get_database_assemblies_envelope_roof(self):
        """scenario/inputs/database/ASSEMBLIES/ENVELOPE/ENVELOPE_ROOF.csv"""
        return os.path.join(self.get_db4_assemblies_envelope_folder(), 'ENVELOPE_ROOF.csv')

    def get_database_assemblies_envelope_shading(self):
        """scenario/inputs/database/ASSEMBLIES/ENVELOPE/ENVELOPE_SHADING.csv"""
        return os.path.join(self.get_db4_assemblies_envelope_folder(), 'ENVELOPE_SHADING.csv')

    def get_database_assemblies_envelope_wall(self):
        """scenario/inputs/database/ASSEMBLIES/ENVELOPE/ENVELOPE_WALL.csv"""
        return os.path.join(self.get_db4_assemblies_envelope_folder(), 'ENVELOPE_WALL.csv')

    def get_db4_assemblies_hvac_folder(self):
        """scenario/inputs/database/ASSEMBLIES/HVAC"""
        return os.path.join(self.get_db4_assemblies_folder(), 'HVAC')

    def get_database_assemblies_hvac_controller(self):
        """scenario/inputs/database/ASSEMBLIES/HVAC/HVAC_CONTROLLER.csv"""
        return os.path.join(self.get_db4_assemblies_hvac_folder(), 'HVAC_CONTROLLER.csv')

    def get_database_assemblies_hvac_heating(self):
        """scenario/inputs/database/ASSEMBLIES/HVAC/HVAC_HEATING.csv"""
        return os.path.join(self.get_db4_assemblies_hvac_folder(), 'HVAC_HEATING.csv')

    def get_database_assemblies_hvac_cooling(self):
        """scenario/inputs/database/ASSEMBLIES/HVAC/HVAC_COOLING.csv"""
        return os.path.join(self.get_db4_assemblies_hvac_folder(), 'HVAC_COOLING.csv')

    def get_database_assemblies_hvac_ventilation(self):
        """scenario/inputs/database/ASSEMBLIES/HVAC/HVAC_VENTILATION.csv"""
        return os.path.join(self.get_db4_assemblies_hvac_folder(), 'HVAC_VENTILATION.csv')

    def get_database_assemblies_hvac_hot_water(self):
        """scenario/inputs/database/ASSEMBLIES/HVAC/HVAC_HOTWATER.csv"""
        return os.path.join(self.get_db4_assemblies_hvac_folder(), 'HVAC_HOTWATER.csv')

    def get_db4_assemblies_supply_folder(self):
        """scenario/inputs/database/ASSEMBLIES/SUPPLY"""
        return os.path.join(self.get_db4_assemblies_folder(), 'SUPPLY')

    def get_database_assemblies_supply_cooling(self):
        """scenario/inputs/database/ASSEMBLIES/SUPPLY/SUPPLY_COOLING.csv"""
        return os.path.join(self.get_db4_assemblies_supply_folder(), 'SUPPLY_COOLING.csv')

    def get_database_assemblies_supply_electricity(self):
        """scenario/inputs/database/ASSEMBLIES/SUPPLY/SUPPLY_ELECTRICITY.csv"""
        return os.path.join(self.get_db4_assemblies_supply_folder(), 'SUPPLY_ELECTRICITY.csv')

    def get_database_assemblies_supply_heating(self):
        """scenario/inputs/database/ASSEMBLIES/SUPPLY/SUPPLY_HEATING.csv"""
        return os.path.join(self.get_db4_assemblies_supply_folder(), 'SUPPLY_HEATING.csv')

    def get_database_assemblies_supply_hot_water(self):
        """scenario/inputs/database/ASSEMBLIES/SUPPLY/SUPPLY_HOTWATER.csv"""
        return os.path.join(self.get_db4_assemblies_supply_folder(), 'SUPPLY_HOTWATER.csv')

    def get_db4_components_folder(self):
        """scenario/inputs/database/COMPONENTS"""
        return os.path.join(self.get_db4_folder(), 'COMPONENTS')

    def get_db4_components_conversion_folder(self):
        """scenario/inputs/database/COMPONENTS/CONVERSION"""
        return os.path.join(self.get_db4_components_folder(), 'CONVERSION')

    def get_db4_components_conversion_conversion_technology_csv(self, conversion_technology):
        """scenario/inputs/database/COMPONENTS/CONVERSION/{conversion_technology}.csv"""
        return os.path.join(self.get_db4_components_conversion_folder(), f'{conversion_technology}.csv')

    def get_db4_components_conversion_technologies_all(self):
        """return: dict of scenario/inputs/database/COMPONENTS/CONVERSION/*.csv"""
        csv_file_names = [os.path.splitext(file)[0] for file in os.listdir(self.get_db4_components_conversion_folder())
                          if file.endswith('.csv')]
        return {name: self.get_db4_components_conversion_conversion_technology_csv(name) for name in csv_file_names}

    def get_db4_components_distribution_folder(self):
        """scenario/inputs/database/COMPONENTS/DISTRIBUTION"""
        return os.path.join(self.get_db4_components_folder(), 'DISTRIBUTION')

    def get_database_components_distribution_thermal_grid(self, distribution="THERMAL_GRID"):
        """scenario/inputs/database/COMPONENTS/DISTRIBUTION/{distribution}.csv"""
        return os.path.join(self.get_db4_components_distribution_folder(), f'{distribution}.csv')

    def get_db4_components_feedstocks_folder(self):
        """scenario/inputs/database/COMPONENTS/FEEDSTOCKS"""
        return os.path.join(self.get_db4_components_folder(), 'FEEDSTOCKS')

    def get_db4_components_feedstocks_library_folder(self):
        """scenario/inputs/database/COMPONENTS/FEEDSTOCKS"""
        return os.path.join(self.get_db4_components_folder(), 'FEEDSTOCKS', 'FEEDSTOCKS_LIBRARY')

    def get_db4_components_feedstocks_feedstocks_csv(self, feedstocks):
        """scenario/inputs/database/COMPONENTS/FEEDSTOCKS/FEEDSTOCKS_LIBRARY/{feedstocks}.csv"""
        return os.path.join(self.get_db4_components_feedstocks_library_folder(), f'{feedstocks}.csv')

    def get_db4_components_feedstocks_all(self):
        """return: dict of scenario/inputs/database/COMPONENTS/FEEDSTOCKS/FEEDSTOCKS_LIBRARY/*.csv"""
        csv_file_names = [os.path.splitext(file)[0] for file in
                          os.listdir(self.get_db4_components_feedstocks_library_folder()) if file.endswith('.csv')]
        return {name: self.get_db4_components_feedstocks_feedstocks_csv(name) for name in csv_file_names}

    def get_database_components_feedstocks_energy_carriers(self):
        """scenario/inputs/database/COMPONENTS/FEEDSTOCKS/ENERGY_CARRIERS.csv"""
        return os.path.join(self.get_db4_components_feedstocks_folder(), 'ENERGY_CARRIERS.csv')

    def get_database_conversion_systems_cold_thermal_storage_names(self):
        """Return the list of thermal storage tanks"""
        if not os.path.exists(self.get_db4_components_conversion_conversion_technology_csv('THERMAL_ENERGY_STORAGES')):
            return []
        import pandas as pd
        data = pd.read_csv(self.get_db4_components_conversion_conversion_technology_csv('THERMAL_ENERGY_STORAGES'))
        data = data[data["type"] == "COOLING"]
        names = sorted(data["code"])
        return names

    def get_building_geometry_folder(self):
        """scenario/inputs/building-geometry/"""
        return os.path.join(self.scenario, 'inputs', 'building-geometry')

    def get_building_properties_folder(self):
        """scenario/inputs/building-properties/"""
        return os.path.join(self.scenario, 'inputs', 'building-properties')

    def get_terrain_folder(self):
        return os.path.join(self.scenario, 'inputs', 'topography')

    def get_tree_geometry_folder(self):
        return os.path.join(self.scenario, 'inputs', 'tree-geometry')

    def get_tree_geometry(self):
        shapefile_path = os.path.join(self.get_tree_geometry_folder(), 'trees.shp')
        check_cpg(shapefile_path)
        return shapefile_path

    def get_zone_geometry(self):
        """scenario/inputs/building-geometry/zone.shp"""
        shapefile_path = os.path.join(self.get_building_geometry_folder(), 'zone.shp')
        check_cpg(shapefile_path)
        return shapefile_path

    def get_site_polygon(self):
        """scenario/inputs/building-geometry/site.shp"""
        shapefile_path = os.path.join(self.get_building_geometry_folder(), 'site.shp')
        check_cpg(shapefile_path)
        return shapefile_path

    def get_surroundings_geometry(self):
        """scenario/inputs/building-geometry/surroundings.shp"""
        # NOTE: we renamed district.shp to surroundings.shp - this code will automatically upgrade old scenarios
        shapefile_path = os.path.join(self.get_building_geometry_folder(), 'surroundings.shp')
        check_cpg(shapefile_path)
        return shapefile_path

    def get_zone_building_names(self):
        """Return the list of buildings in the Zone"""
        if not os.path.exists(self.get_zone_geometry()):
            return []
        import geopandas as gdf
        zone_building_names = sorted(gdf.read_file(self.get_zone_geometry())['name'].values)
        return zone_building_names

    def get_building_supply(self):
        """scenario/inputs/building-properties/supply.csv"""
        return os.path.join(self.get_building_properties_folder(), 'supply.csv')

    def get_building_internal(self):
        """scenario/inputs/building-properties/internal_loads.csv"""
        return os.path.join(self.get_building_properties_folder(), 'internal_loads.csv')

    def get_building_comfort(self):
        """scenario/inputs/building-properties/indoor_comfort.csv"""
        return os.path.join(self.get_building_properties_folder(), 'indoor_comfort.csv')

    def get_building_air_conditioning(self):
        """scenario/inputs/building-properties/hvac.csv"""
        return os.path.join(self.get_building_properties_folder(), 'hvac.csv')

    def get_building_architecture(self):
        """scenario/inputs/building-properties/envelope.csv
        This file is generated by the data-helper script.
        This file is used in the embodied energy script (cea/embodied.py)
        and the demand script (cea/demand_main.py)"""
        return os.path.join(self.get_building_properties_folder(), 'envelope.csv')

    def get_building_weekly_schedules_folder(self):
        """scenario/inputs/building-properties/schedules/"""
        return os.path.join(self.get_building_properties_folder(), 'schedules')

    def get_building_weekly_schedules_monthly_multiplier_csv(self):
        """
        scenario/inputs/building-properties/schedules/MONTHLY_MULTIPLIERS.csv"""
        return os.path.join(self.get_building_weekly_schedules_folder(), 'MONTHLY_MULTIPLIERS.csv')

    def get_building_weekly_schedules(self, building):
        """
        scenario/inputs/building-properties/schedules/{building}.csv
        This file contains schedules of occupancy, appliance use, etc of each building.

        The format is a bit weird (e.g. not strictly a CSV table):

        First row contains two columns (METADATA, <schedule-type>
        Second row contains 13 columns (MONTHLY_MULTIPLIER, <jan-multiplier>, <feb-multiplier>, etc.)
        The following rows are three sets of HOUR 1-24, one set for each of DAY in {WEEKDAY, SATURDAY, SUNDAY}

        These weekly schedules are used by the occupancy-helper script to create the schedules for each hour of the
        year (``get_occupancy_model_file``).

        Do not read this file yourself, instead, use :py:func`cea.utilities.schedule_reader.read_cea_schedule`

        :param str building: The building to create the schedule for
        :return:
        """
        return os.path.join(self.get_building_weekly_schedules_folder(), '{}.csv'.format(building))

    def get_occupancy_model_folder(self):
        """scenario/outputs/data/occupancy
        Folder to store occupancy to.
        """
        return os.path.join(self.scenario, 'outputs', 'data', 'occupancy')

    def get_occupancy_model_file(self, building):
        """
        scenario/outputs/data/occupancy/{building}.csv

        This file contains occupancy information of each building.
        Occupancy info has 8760 values per year
        :param building: The building to get the occupancy file for.
        :return:
        """
        return os.path.join(self.get_occupancy_model_folder(), '{}.csv'.format(building))

    def get_terrain(self):
        """scenario/inputs/topography/terrain.tif"""
        return os.path.join(self.get_terrain_folder(), 'terrain.tif')

    def get_output_thermal_network_type_folder(self, network_type, network_name=""):
        if network_name == '':  # in case there is no specific network name (default case)
            return os.path.join(self.get_thermal_network_folder(), network_type)
        else:
            return os.path.join(self.get_thermal_network_folder(), network_type, network_name)

    def get_network_layout_edges_shapefile(self, network_type, network_name=""):
        """scenario/outputs/thermal-network/DH or DC/edges.shp"""
        shapefile_path = os.path.join(self.get_output_thermal_network_type_folder(network_type, network_name), 'edges.shp')
        check_cpg(shapefile_path)
        return shapefile_path

    def get_network_layout_nodes_shapefile(self, network_type, network_name=""):
        """scenario/outputs/thermal-network/DH or DC/nodes.shp"""
        shapefile_path = os.path.join(self.get_output_thermal_network_type_folder(network_type, network_name), 'nodes.shp')
        check_cpg(shapefile_path)
        return shapefile_path

    # THERMAL NETWORK OUTPUTS
    def get_thermal_network_folder(self):
        return os.path.join(self.scenario, 'outputs', 'data', 'thermal-network')

    def get_nominal_edge_mass_flow_csv_file(self, network_type, network_name=""):
        """scenario/outputs/data/optimization/network/layout/DH_NodesData.csv or DC_NodesData.csv
        Network layout files for nodes of district heating or cooling networks
        """
        if not network_name:
            file_name = 'Nominal_EdgeMassFlow_at_design_' + network_type + '_' + '_kgpers.csv'
        else:
            file_name = 'Nominal_EdgeMassFlow_at_design_' + network_type + '_' + network_name + '_kgpers.csv'

        return os.path.join(self.get_thermal_network_folder(), file_name)

    def get_nominal_node_mass_flow_csv_file(self, network_type, network_name=""):
        """scenario/outputs/data/optimization/network/layout/DH_NodesData.csv or DC_NodesData.csv
        Network layout files for nodes of district heating or cooling networks
        """
        if not network_name:
            file_name = 'Nominal_NodeMassFlow_at_design_' + network_type + '_' + '_kgpers.csv'
        else:
            file_name = 'Nominal_NodeMassFlow_at_design_' + network_type + '_' + network_name + '_kgpers.csv'

        return os.path.join(self.get_thermal_network_folder(), file_name)

    def get_thermal_network_edge_node_matrix_file(self, network_type, network_name=""):
        """scenario/outputs/data/optimization/network/layout/DH_EdgeNode.csv or DC_EdgeNode.csv
        Edge-node matrix for a heating or cooling network
        """
        if network_name:
            file_name = network_type + "_" + network_name + "_EdgeNode.csv"
        else:
            file_name = network_type + "_" + "_EdgeNode.csv"
        return os.path.join(self.get_thermal_network_folder(), file_name)

    def get_thermal_network_node_types_csv_file(self, network_type, network_name):
        """scenario/outputs/data/optimization/network/layout/DH_Nodes.csv or DC_NodesData.csv
        Network layout files for nodes of district heating or cooling networks
        """
        if not network_name:
            file_name = network_type + '_' + "_metadata_nodes.csv"
        else:
            file_name = network_type + '_' + network_name + '_metadata_nodes.csv'

        return os.path.join(self.get_thermal_network_folder(), file_name)

    def get_plant_nodes(self, network_type, network_name):
        """Return the list of "PLANT" nodes in a thermal network"""
        nodes_csv = self.get_thermal_network_node_types_csv_file(network_type, network_name)
        if os.path.exists(nodes_csv):
            import pandas as pd
            nodes_df = pd.read_csv(nodes_csv)
            is_plant = nodes_df['Type'] == 'PLANT'
            return nodes_df[is_plant]['name'].to_list()
        return []

    def get_thermal_network_edge_list_file(self, network_type, network_name=''):
        """scenario/outputs/data/optimization/network/layout/DH_AllEdges.csv or DC_AllEdges.csv
        List of edges in a district heating or cooling network and their start and end nodes
        """
        if not network_name:
            file_name = network_type + "_" + "_metadata_edges.csv"
        else:
            file_name = network_type + "_" + network_name + "_metadata_edges.csv"
        return os.path.join(self.get_thermal_network_folder(), file_name)

    def get_representative_week_thermal_network_layout_folder(self):
        """scenario/outputs/data/optimization/network/layout
        Network layout files
        """
        return os.path.join(self.get_thermal_network_folder(), "reduced_timesteps")

    def get_thermal_network_layout_massflow_edges_file(self, network_type, network_name, representative_week=False):
        """scenario/outputs/data/optimization/network/layout/DH_MassFlow.csv or DC_MassFlow.csv
        Mass flow rates at each edge in a district heating or cooling network
        """
        if representative_week:
            folder = self.get_representative_week_thermal_network_layout_folder()
        else:
            folder = self.get_thermal_network_folder()
        if not network_name:
            file_name = network_type + "_" + "_massflow_edges_kgs.csv"
        else:
            file_name = network_type + "_" + network_name + "_massflow_edges_kgs.csv"
        return os.path.join(folder, file_name)

    def get_thermal_network_velocity_edges_file(self, network_type, network_name, representative_week=False):
        """scenario/outputs/data/optimization/network/layout/DH_MassFlow.csv or DC_MassFlow.csv
        Mass flow rates at each edge in a district heating or cooling network
        """
        if representative_week:
            folder = self.get_representative_week_thermal_network_layout_folder()
        else:
            folder = self.get_thermal_network_folder()
        if not network_name:
            file_name = network_type + "_" + "_velocity_edges_mpers.csv"
        else:
            file_name = network_type + "_" + network_name + "_velocity_edges_mpers.csv"
        return os.path.join(folder, file_name)

    def get_thermal_network_layout_massflow_nodes_file(self, network_type, network_name, representative_week=False):
        """scenario/outputs/data/optimization/network/layout/DH_MassFlow.csv or DC_MassFlow.csv
        Mass flow rates at each edge in a district heating or cooling network
        """
        if representative_week:
            folder = self.get_representative_week_thermal_network_layout_folder()
        else:
            folder = self.get_thermal_network_folder()
        if not network_name:
            file_name = network_type + "_" + "_massflow_nodes_kgs.csv"
        else:
            file_name = network_type + "_" + network_name + "_massflow_nodes_kgs.csv"
        return os.path.join(folder, file_name)

    def get_network_temperature_supply_nodes_file(self, network_type, network_name,
                                                  representative_week=False):
        """scenario/outputs/data/optimization/network/layout/DH_T_Supply.csv or DC_T_Supply.csv
        Supply temperatures at each node for each time step for a district heating or cooling network
        """
        if representative_week:
            folder = self.get_representative_week_thermal_network_layout_folder()
        else:
            folder = self.get_thermal_network_folder()
        if not network_name:
            file_name = network_type + "_" + "_temperature_supply_nodes_K.csv"
        else:
            file_name = network_type + "_" + network_name + "_temperature_supply_nodes_K.csv"
        return os.path.join(folder, file_name)

    def get_network_temperature_return_nodes_file(self, network_type, network_name,
                                                  representative_week=False):
        """scenario/outputs/data/optimization/network/layout/DH_T_Return.csv or DC_T_Return.csv
        Return temperatures at each node for each time step for a district heating or cooling network
        """
        if representative_week:
            folder = self.get_representative_week_thermal_network_layout_folder()
        else:
            folder = self.get_thermal_network_folder()
        if not network_name:
            file_name = network_type + "_" + "_temperature_return_nodes_K.csv"
        else:
            file_name = network_type + "_" + network_name + "_temperature_return_nodes_K.csv"
        return os.path.join(folder, file_name)

    def get_network_temperature_plant(self, network_type, network_name,
                                      representative_week=False):

        if representative_week:
            folder = self.get_representative_week_thermal_network_layout_folder()
        else:
            folder = self.get_thermal_network_folder()
        if not network_name:
            file_name = network_type + "_" + "_temperature_plant_K.csv"
        else:
            file_name = network_type + "_" + network_name + "_temperature_plant_K.csv"
        return os.path.join(folder, file_name)

    def get_thermal_network_substation_ploss_file(self, network_type, network_name, representative_week=False):
        """scenario/outputs/data/optimization/network/layout/DH_qloss_substations_kw.csv"""
        if representative_week:
            folder = self.get_representative_week_thermal_network_layout_folder()
        else:
            folder = self.get_thermal_network_folder()
        if not network_name:
            file_name = network_type + "_" + "_pumping_load_due_to_substations_kW.csv"
        else:
            file_name = network_type + "_" + network_name + "_pumping_load_due_to_substations_kW.csv"
        return os.path.join(folder, file_name)

    def get_thermal_demand_csv_file(self, network_type, network_name, representative_week=False):
        """scenario/outputs/data/optimization/network/layout/DH_NodesData.csv or DC_NodesData.csv
        Network layout files for nodes of district heating or cooling networks
        """
        if representative_week:
            folder = self.get_representative_week_thermal_network_layout_folder()
        else:
            folder = self.get_thermal_network_folder()

        if not network_name:
            file_name = network_type + "_" + "_thermal_demand_per_building_W.csv"
        else:
            file_name = network_type + "_" + network_name + "_thermal_demand_per_building_W.csv"
        return os.path.join(folder, file_name)

    def get_network_thermal_loss_edges_file(self, network_type, network_name, representative_week=False):
        """scenario/outputs/data/optimization/network/layout/DH_qloss_System_kw.csv"""
        if representative_week:
            folder = self.get_representative_week_thermal_network_layout_folder()
        else:
            folder = self.get_thermal_network_folder()
        if not network_name:
            file_name = network_type + "_" + "_thermal_loss_edges_kW.csv"
        else:
            file_name = network_type + "_" + network_name + "_thermal_loss_edges_kW.csv"
        return os.path.join(folder, file_name)

    def get_network_linear_thermal_loss_edges_file(self, network_type, network_name, representative_week=False):
        """scenario/outputs/data/optimization/network/layout/DH_qloss_System_kw.csv"""
        if representative_week:
            folder = self.get_representative_week_thermal_network_layout_folder()
        else:
            folder = self.get_thermal_network_folder()
        if not network_name:
            file_name = network_type + "_" + "_linear_thermal_loss_edges_Wperm.csv"
        else:
            file_name = network_type + "_" + network_name + "_linear_thermal_loss_edges_Wperm.csv"
        return os.path.join(folder, file_name)

    def get_network_total_thermal_loss_file(self, network_type, network_name, representative_week=False):
        """scenario/outputs/data/optimization/network/layout/DH_qloss_System_kw.csv"""
        if representative_week:
            folder = self.get_representative_week_thermal_network_layout_folder()
        else:
            folder = self.get_thermal_network_folder()
        if not network_name:
            file_name = network_type + "_" + "_total_thermal_loss_edges_kW.csv"
        else:
            file_name = network_type + "_" + network_name + "_total_thermal_loss_edges_kW.csv"
        return os.path.join(folder, file_name)

    def get_thermal_network_pressure_losses_edges_file(self, network_type, network_name,
                                                       representative_week=False):
        """scenario/outputs/data/optimization/network/layout/DH_qloss_System_kw.csv"""
        if representative_week:
            folder = self.get_representative_week_thermal_network_layout_folder()
        else:
            folder = self.get_thermal_network_folder()
        if not network_name:
            file_name = network_type + "_" + "_pressure_losses_edges_kW.csv"
        else:
            file_name = network_type + "_" + network_name + "_pressure_losses_edges_kW.csv"
        return os.path.join(folder, file_name)

    def get_network_total_pressure_drop_file(self, network_type, network_name, representative_week=False):
        """scenario/outputs/data/optimization/network/layout/DH_P_DeltaP.csv or DC_P_DeltaP.csv
        Pressure drop over an entire district heating or cooling network at each time step
        """
        if representative_week:
            folder = self.get_representative_week_thermal_network_layout_folder()
        else:
            folder = self.get_thermal_network_folder()
        if not network_name:
            file_name = network_type + "_" + "_plant_pumping_pressure_loss_Pa.csv"
        else:
            file_name = network_type + "_" + network_name + "_plant_pumping_pressure_loss_Pa.csv"
        return os.path.join(folder, file_name)

    def get_network_linear_pressure_drop_edges(self, network_type, network_name, representative_week=False):
        """scenario/outputs/data/optimization/network/layout/DH_P_DeltaP.csv or DC_P_DeltaP.csv
        Pressure drop over an entire district heating or cooling network at each time step
        """
        if representative_week:
            folder = self.get_representative_week_thermal_network_layout_folder()
        else:
            folder = self.get_thermal_network_folder()
        if not network_name:
            file_name = network_type + "_" + "_linear_pressure_drop_edges_Paperm.csv"
        else:
            file_name = network_type + "_" + network_name + "_linear_pressure_drop_edges_Paperm.csv"
        return os.path.join(folder, file_name)

    def get_network_pressure_at_nodes(self, network_type, network_name, representative_week=False):
        """scenario/outputs/data/optimization/network/layout/DH_P_DeltaP.csv or DC_P_DeltaP.csv
        Pressure drop over an entire district heating or cooling network at each time step
        """
        if representative_week:
            folder = self.get_representative_week_thermal_network_layout_folder()
        else:
            folder = self.get_thermal_network_folder()
        if not network_name:
            file_name = network_type + "_" + "_pressure_at_nodes_Pa.csv"
        else:
            file_name = network_type + "_" + network_name + "_pressure_at_nodes_Pa.csv"
        return os.path.join(folder, file_name)

    def get_network_energy_pumping_requirements_file(self, network_type, network_name,
                                                     representative_week=False):
        """scenario/outputs/data/optimization/network/layout/DH_P_DeltaP.csv or DC_P_DeltaP.csv
        Pressure drop over an entire district heating or cooling network at each time step
        """
        if representative_week:
            folder = self.get_representative_week_thermal_network_layout_folder()
        else:
            folder = self.get_thermal_network_folder()
        if not network_name:
            file_name = network_type + "_" + "_plant_pumping_load_kW.csv"
        else:
            file_name = network_type + "_" + network_name + "_plant_pumping_load_kW.csv"
        return os.path.join(folder, file_name)

    def get_thermal_network_plant_heat_requirement_file(self, network_type, network_name,
                                                        representative_week=False):
        """scenario/outputs/data/optimization/network/layout/DH_Plant_heat_requirement.csv or DC_Plant_heat_requirement.csv
        Heat requirement at from the plants in a district heating or cooling network
        """
        if representative_week:
            folder = self.get_representative_week_thermal_network_layout_folder()
        else:
            folder = self.get_thermal_network_folder()
        if not network_name:
            file_name = network_type + "_" + "_plant_thermal_load_kW.csv"
        else:
            file_name = network_type + "_" + network_name + "_plant_thermal_load_kW.csv"
        return os.path.join(folder, file_name)

    def get_networks_folder(self):
        return os.path.join(self.scenario, 'inputs', 'networks')

    def get_street_network(self):
        shapefile_path = os.path.join(self.get_networks_folder(), "streets.shp")
        check_cpg(shapefile_path)
        return shapefile_path

    # OUTPUTS

    # SOLAR-RADIATION
    def get_solar_radiation_folder(self):
        """scenario/outputs/data/solar-radiation"""
        return os.path.join(self.scenario, 'outputs', 'data', 'solar-radiation')

    def get_radiation_building(self, building):
        """scenario/outputs/data/solar-radiation/${building}_radiation.csv"""
        return os.path.join(self.get_solar_radiation_folder(), '%s_radiation.csv' % building)

    def get_radiation_building_sensors(self, building):
        """scenario/outputs/data/solar-radiation/${building}_insolation_Whm2.feather"""
        return os.path.join(self.get_solar_radiation_folder(), '%s_insolation_Whm2.feather' % building)

    def get_radiation_metadata(self, building):
        """scenario/outputs/data/solar-radiation/{building}_geometrgy.csv"""
        return os.path.join(self.get_solar_radiation_folder(), '%s_geometry.csv' % building)

    def get_radiation_materials(self):
        """scenario/outputs/data/solar-radiation/{building}_geometry.csv"""
        return os.path.join(self.get_solar_radiation_folder(), 'buidling_materials.csv')

    def solar_potential_folder(self):
        return os.path.join(self.scenario, 'outputs', 'data', 'potentials', 'solar')

    def solar_potential_folder_PV(self):
        """scenario/outputs/data/potentials/solar/PV"""
        return os.path.join(self.scenario, 'outputs', 'data', 'potentials', 'solar', 'PV')

    def solar_potential_folder_SC(self):
        """scenario/outputs/data/potentials/solar/SC"""
        return os.path.join(self.scenario, 'outputs', 'data', 'potentials', 'solar', 'SC')

    def solar_potential_folder_PVT(self):
        """scenario/outputs/data/potentials/solar/PVT"""
        return os.path.join(self.scenario, 'outputs', 'data', 'potentials', 'solar', 'PVT')

    def solar_potential_folder_sensors(self):
        return os.path.join(self.scenario, 'outputs', 'data', 'potentials', 'solar', 'sensors')

    def PV_results(self, building, panel_type):
        """scenario/outputs/data/potentials/solar/PV/{building}_{panel_type}.csv"""
        return os.path.join(self.solar_potential_folder_PV(),
                            "{building}_{panel_type}.csv".format(building=building, panel_type=panel_type))

    def PV_totals(self, panel_type):
        """scenario/outputs/data/potentials/solar/{building}_PV_{panel_type}_total.csv.csv"""
        return os.path.join(self.solar_potential_folder(), "PV_{panel_type}_total.csv".format(panel_type=panel_type))

    def PV_total_buildings(self, panel_type):
        """scenario/outputs/data/potentials/solar/{building}_PV_{panel_type}_total_buildings.csv"""
        return os.path.join(self.solar_potential_folder(), 'PV_%s_total_buildings.csv' % panel_type)

    def PV_metadata_results(self, building):
        """scenario/outputs/data/potentials/solar/{building}_PV_sensors.csv"""
        return os.path.join(self.solar_potential_folder_sensors(),
                            "{building}_PV_sensors.csv".format(building=building))

    def SC_results(self, building, panel_type):
        """scenario/outputs/data/potentials/solar/SC/{building}_{panel_type}.csv"""
        return os.path.join(self.solar_potential_folder_SC(), f"{building}_{panel_type}.csv")

    def SC_totals(self, panel_type):
        """scenario/outputs/data/potentials/solar/SC_{panel_type}_total.csv"""
        return os.path.join(self.solar_potential_folder(), "SC_{panel_type}_total.csv".format(panel_type=panel_type))

    def SC_total_buildings(self, panel_type):
        """scenario/outputs/data/potentials/solar/SC_{panel_type}_total_buildings.csv"""
        return os.path.join(self.solar_potential_folder(), 'SC_%s_total_buildings.csv' % panel_type)

    def SC_metadata_results(self, building, panel_type):
        """scenario/outputs/data/potentials/solar/{building}_SC_sensors.csv"""
        return os.path.join(self.solar_potential_folder_sensors(), '%s_SC_%s_sensors.csv' % (building, panel_type))

    def PVT_results(self, building, pv_panel_type, sc_panel_type):
        return os.path.join(self.solar_potential_folder_PVT(), f"{building}_{pv_panel_type}_{sc_panel_type}.csv")

    def PVT_totals(self, pv_panel_type, sc_panel_type):
        return os.path.join(self.solar_potential_folder(), f'PVT_{pv_panel_type}_{sc_panel_type}_total.csv')

    def PVT_total_buildings(self, pv_panel_type, sc_panel_type):
        return os.path.join(self.solar_potential_folder(), f'PVT_{pv_panel_type}_{sc_panel_type}_total_buildings.csv')

    def PVT_metadata_results(self, building):
        """scenario/outputs/data/potentials/solar/{building}_SC_sensors.csv"""
        return os.path.join(self.solar_potential_folder_sensors(), '%s_PVT_sensors.csv' % building)

    # DEMAND

    def get_demand_results_folder(self):
        """scenario/outputs/data/demand"""
        return os.path.join(self.scenario, 'outputs', 'data', 'demand')

    def get_total_demand(self, format='csv'):
        """scenario/outputs/data/demand/Total_demand.csv"""
        return os.path.join(self.get_demand_results_folder(), 'Total_demand.%(format)s' % locals())

    def get_total_demand_hourly(self, format='csv'):
        """scenario/outputs/data/demand/Total_demand_hourly.csv"""
        return os.path.join(self.get_demand_results_folder(), 'Total_demand_hourly.%(format)s' % locals())

    def get_demand_results_file(self, building, format='csv'):
        """scenario/outputs/data/demand/{building}.csv"""
        return os.path.join(self.get_demand_results_folder(), '%(building)s.%(format)s' % locals())

    # EMISSIONS
    def get_lca_emissions_results_folder(self):
        """scenario/outputs/data/emissions"""
        return os.path.join(self.scenario, 'outputs', 'data', 'emissions')

    def get_lca_embodied(self):
        """scenario/outputs/data/emissions/Total_LCA_embodied.csv"""
        return os.path.join(self.get_lca_emissions_results_folder(), 'Simplified_LCA_embodied_selected_year.csv')

    def get_lca_operation(self):
        """scenario/outputs/data/emissions/Total_emissions_operation.csv"""
        return os.path.join(self.get_lca_emissions_results_folder(), 'Simplified_LCA_operational_selected_year.csv')

    def get_lca_mobility(self):
        """scenario/outputs/data/emissions/Total_LCA_mobility.csv"""
        return os.path.join(self.get_lca_emissions_results_folder(), 'Total_LCA_mobility.csv')
    
    def get_lca_timeline_folder(self):
        """scenario/outputs/data/emissions/timeline"""
        return os.path.join(self.get_lca_emissions_results_folder(), "timeline")

    def get_total_yearly_operational_building(self):
        """scenario/outputs/data/emissions/timeline/Total_yearly_operational_building.csv"""
        return os.path.join(self.get_lca_timeline_folder(), "Total_yearly_operational_building.csv")

    def get_total_yearly_operational_hour(self):
        """scenario/outputs/data/emissions/timeline/Total_yearly_operational.csv"""
        return os.path.join(self.get_lca_timeline_folder(), "Total_yearly_operational.csv")

    def get_total_emissions_building_year_end(self, year_end):
        """scenario/outputs/data/emissions/timeline/Total_emission_building_{year_end}.csv"""
        return os.path.join(
            self.get_lca_timeline_folder(), f"Total_emission_building_{year_end}.csv")

    def get_total_emissions_timeline_year_end(self, year_end):
        """scenario/outputs/data/emissions/timeline/Total_emission_timeline_{year_end}.csv"""
        return os.path.join(self.get_lca_timeline_folder(), f"Total_emission_timeline_{year_end}.csv")
    
    def get_lca_timeline_building(self, building: str):
        """scenario/outputs/data/emissions/timeline/{building}_timeline.csv"""
        return os.path.join(self.get_lca_timeline_folder(), f"{building}_timeline.csv")

    def get_lca_operational_hourly_building(self, building: str):
        """scenario/outputs/data/emissions/timeline/{building}_operational_hourly.csv"""
        return os.path.join(self.get_lca_timeline_folder(), f"{building}_operational_hourly.csv")

    # COSTS
    def get_costs_folder(self):
        """scenario/outputs/data/costs"""
        return os.path.join(self.scenario, 'outputs', 'data', 'costs')

    def get_multi_criteria_results_folder(self):
        """scenario/outputs/data/multi-criteria"""
        return os.path.join(self.scenario, 'outputs', 'data', 'multicriteria')

    def get_multi_criteria_analysis(self, generation):
        return os.path.join(self.get_multi_criteria_results_folder(),
                            'gen_' + str(generation) + '_multi_criteria_analysis.csv')

    # RETROFIT POTENTIAL

    def get_costs_operation_file(self):
        """scenario/outputs/data/costs/{load}_cost_operation.pdf"""
        return os.path.join(self.get_costs_folder(), 'supply_system_costs_today.csv')

    # GRAPHS
    def get_plots_folder(self, category):
        """scenario/outputs/plots/timeseries"""
        return os.path.join(self.scenario, 'outputs', 'plots', category)

    def get_timeseries_plots_file(self, building, category=''):
        """scenario/outputs/plots/timeseries/{building}.html
        :param category:
        """
        return os.path.join(self.get_plots_folder(category), '%(building)s.html' % locals())

    # OTHER
    def get_temporary_folder(self):
        """Temporary folder as returned by `tempfile`."""
        return self._temp_directory

    def get_temporary_file(self, filename):
        """Returns the path to a file in the temporary folder with the name `filename`"""
        return os.path.join(self.get_temporary_folder(), filename)


def check_cpg(shapefile_path: str) -> None:
    """Ensures that the accompanied CPG file is the correct, and create one if it does not exist"""
    # Ignore if not file or does not exist
    if not os.path.isfile(shapefile_path):
        return

    import fiona

    # Use common encodings for .dbf files
    encoding_list = ["ISO-8859-1", "UTF-8"]

    cpg_file_path = f"{os.path.splitext(shapefile_path)[0]}.cpg"
    if os.path.exists(cpg_file_path):
        # If the CPG file exists, try to open it with the provided encoding (use None for original encoding)
        encoding_list.insert(0, None)

    for encoding in encoding_list:
        try:
            with fiona.open(shapefile_path, encoding=encoding) as layer:
                # Access metadata to test encoding
                _ = layer.schema['properties']

                # Write the encoding to the CPG file if original encoding is not provided / invalid
                if encoding is not None:
                    print("Writing correct cpg")
                    with open(cpg_file_path, "w") as cpg_file:
                        cpg_file.write(encoding)

                return
        except UnicodeDecodeError as e:
            print(f"Encoding '{encoding}' failed: {e}")

    raise ValueError(f"Could not find a valid encoding for the .shp file '{shapefile_path}'.")


class ReferenceCaseOpenLocator(InputLocator):
    """This is a special InputLocator that extracts the builtin reference case
    (``cea/examples/reference-case-open.zip``) to the temporary folder and uses the baseline scenario in there"""

    def __init__(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        atexit.register(self.temp_directory.cleanup)

        self.project_path = os.path.join(self.temp_directory.name, 'reference-case-open')
        reference_case = os.path.join(self.project_path, 'baseline')

        import cea.examples
        import zipfile
        with zipfile.ZipFile(os.path.join(os.path.dirname(cea.examples.__file__), 'reference-case-open.zip')) as archive:
            archive.extractall(self.temp_directory.name)

        #FIXME: Remove this once reference-case-open is updated
        from cea.datamanagement.format_helper.cea4_migrate_db import migrate_cea3_to_cea4_db
        from cea.datamanagement.format_helper.cea4_migrate import migrate_cea3_to_cea4
        print("Migrating reference case from v3 to v4")
        migrate_cea3_to_cea4(reference_case)
        migrate_cea3_to_cea4_db(reference_case)

        super(ReferenceCaseOpenLocator, self).__init__(scenario=reference_case)

    def get_default_weather(self):
        """The reference-case-open uses the Zug weather file..."""
        return self.get_weather('Zug-inducity_1990_2010_TMY')
