"""
inputlocator.py - locate input files by name based on the reference folder structure.
"""

import os
import cea.schemas
import shutil
import tempfile
import time

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas", "Jimeno A. Fonseca", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


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

        self._temp_directory = tempfile.TemporaryDirectory()

    def __del__(self):
        self._temp_directory.cleanup()

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
    def _ensure_folder(*components):
        """Return the `*components` joined together as a path to a folder and ensure that that folder exists on disc.
        If it doesn't exist yet, attempt to make it with `os.makedirs`."""
        folder = os.path.join(*components)
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
            except OSError as e:
                time.sleep(0.5)
                if not os.path.exists(folder):
                    raise e
        return folder

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

    def verify_database_template(self):
        """True, if the path is a valid template path - containing the same excel files as the standard regions."""
        default_template = os.path.join(self.db_path, 'CH')
        missing_files = []
        for folder in os.listdir(default_template):
            if os.path.isdir(os.path.join(default_template, folder)):
                # check inside folders
                for file in os.listdir(os.path.join(default_template, folder)):
                    default_file_path = os.path.join(default_template, folder, file)
                    if os.path.isfile(default_file_path) and os.path.splitext(default_file_path)[1] in {'.xls',
                                                                                                        '.xlsx'}:
                        # we're only interested in the excel files
                        template_file_path = os.path.join(self.get_databases_folder(), folder, file)
                        if not os.path.exists(template_file_path):
                            missing_files.append(template_file_path)
        if len(missing_files):
            message = "Invalid database template - files not found: \n{}".format(', \n'.join(missing_files))
            raise IOError(message)
        return True

    def get_input_folder(self):
        """Returns the inputs folder of a scenario"""
        return os.path.join(self.scenario, "inputs")

    def get_optimization_results_folder(self):
        """Returns the folder containing the scenario's optimization results"""
        return self._ensure_folder(self.scenario, 'outputs', 'data', 'optimization')

    def get_electrical_and_thermal_network_optimization_results_folder(self):
        """scenario/outputs/data/optimization"""
        return self._ensure_folder(self.get_optimization_results_folder(), 'electrical_and_thermal_network')

    def get_optimization_master_results_folder(self):
        """Returns the folder containing the scenario's optimization Master Checkpoints"""
        return self._ensure_folder(self.get_optimization_results_folder(), "master")

    def get_optimization_slave_results_folder(self):
        """Returns the folder containing the scenario's optimization Slave results (storage + operation pattern)"""
        return self._ensure_folder(self.get_optimization_results_folder(), "slave")

    def get_optimization_slave_generation_results_folder(self, gen_num):
        """Returns the folder containing the scenario's optimization Slave results (storage + operation pattern)"""
        return self._ensure_folder(
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
        return self._ensure_folder(self.get_optimization_results_folder(), "network")

    def get_optimization_network_layout_folder(self):
        """scenario/outputs/data/optimization/network/layout
        Network layout files
        """
        return self._ensure_folder(self.get_optimization_network_results_folder(), "layout")

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
        return self._ensure_folder(self.get_optimization_results_folder(), "decentralized")

    def get_optimization_checkpoint(self, generation):
        """scenario/outputs/data/optimization/master/..."""
        return os.path.join(self.get_optimization_master_results_folder(),
                            'CheckPoint_' + str(generation) + ".json")

    def get_optimization_substations_folder(self):
        """scenario/outputs/data/optimization/substations
        Substation results for decentralized buildings"""
        return self._ensure_folder(self.get_optimization_results_folder(), "substations")

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
    def get_new_optimization_results_folder(self):
        """Returns the folder containing the scenario's results for the new optimization script"""
        return self._ensure_folder(self.scenario, 'outputs', 'data', 'optimization_new')

    def get_new_optimization_base_case_folder(self, network_type):
        """Returns the folder containing the base-case energy systems against which optimal systems are compared"""
        return self._ensure_folder(self.get_new_optimization_results_folder(), f'base_{network_type}S')

    def get_new_optimization_optimal_district_energy_system_folder(self, district_energy_system_id='DES_000'):
        """Returns the results-folder for the n-th near pareto-optimal district energy system"""
        return self._ensure_folder(self.get_new_optimization_results_folder(),
                                   f'{district_energy_system_id}')

    def get_new_optimization_optimal_networks_folder(self, district_energy_system_id='DES_000'):
        """Returns the results-folder for the i-th network of the n-th near-pareto-optimal DES"""
        des_folder = self.get_new_optimization_optimal_district_energy_system_folder(district_energy_system_id)
        return self._ensure_folder(des_folder, 'networks')

    def get_new_optimization_optimal_network_layout_file(self, district_energy_system_id='DES_000',
                                                         network_id='N0000'):
        """Returns the result-path for the layout of the i-th network of the n-th near-pareto-optimal DES"""
        network_folder = self.get_new_optimization_optimal_networks_folder(district_energy_system_id)
        return os.path.join(network_folder, f'{network_id}_layout.geojson')

    def get_new_optimization_optimal_supply_systems_folder(self, district_energy_system_id='DES_000'):
        """Returns the results-file for the general supply systems results of the n-th near-pareto-optimal DES"""
        des_folder = self.get_new_optimization_optimal_district_energy_system_folder(district_energy_system_id)
        return self._ensure_folder(des_folder, 'Supply_systems')

    def get_new_optimization_optimal_supply_system_file(self, district_energy_system_id='DES_000',
                                                        supply_system_id='N0000_or_B0000'):
        """Returns the results-file for the supply systems summary of the n-th near-pareto-optimal DES"""
        des_supsys_folder = self.get_new_optimization_optimal_supply_systems_folder(district_energy_system_id)
        return os.path.join(des_supsys_folder, f'{supply_system_id}_supply_system_structure.csv')

    def get_new_optimization_optimal_supply_systems_summary_file(self, district_energy_system_id='DES_000'):
        """Returns the results-file for the supply systems summary of the n-th near-pareto-optimal DES"""
        des_supsys_folder = self.get_new_optimization_optimal_supply_systems_folder(district_energy_system_id)
        return os.path.join(des_supsys_folder, 'Supply_systems_summary.csv')

    def get_new_optimization_supply_system_details_folder(self, district_energy_system_id='DES_000'):
        """Returns the results-folder for the detailed supply system information of the n-th near-pareto-optimal DES"""
        des_folder = self.get_new_optimization_optimal_district_energy_system_folder(district_energy_system_id)
        return self._ensure_folder(des_folder, 'Supply_system_operation_details')

    def get_new_optimization_detailed_network_performance_file(self, district_energy_system_id='DES_000'):
        """Returns the results-file for the detailed performance of the n-th near-pareto-optimal DES's networks"""
        des_details_folder = self.get_new_optimization_supply_system_details_folder(district_energy_system_id)
        return os.path.join(des_details_folder, 'network_performance.csv')

    def get_new_optimization_supply_systems_detailed_operation_file(self, district_energy_system_id='DES_000',
                                                                    supply_system_id='N0000_or_B0000'):
        """Returns the results-file for the supply systems operation profiles of the n-th near-pareto-optimal DES"""
        des_details_folder = self.get_new_optimization_supply_system_details_folder(district_energy_system_id)
        return os.path.join(des_details_folder, f'{supply_system_id}_operation.csv')

    def get_new_optimization_supply_systems_annual_breakdown_file(self, district_energy_system_id='DES_000',
                                                                     supply_system_id='N0000_or_B0000'):
        """Returns the results-file for the breakdown of a supply systems annual operation (in terms of energy demand,
        cost, GHG- and heat-emissions) in the n-th near-pareto-optimal DES"""
        des_details_folder = self.get_new_optimization_supply_system_details_folder(district_energy_system_id)
        return os.path.join(des_details_folder, f'{supply_system_id}_annual_breakdown.csv')

    def get_new_optimization_debugging_folder(self):
        """Returns the debugging-folder, used to store information gathered by the optimisation tracker"""
        return self._ensure_folder(self.get_new_optimization_results_folder(), 'debugging')

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
        return self._ensure_folder(self.scenario, 'outputs', 'data', 'potentials')

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
        weather_names = [os.path.splitext(f)[0] for f in os.listdir(self.weather_path)]
        return weather_names

    def get_weather_folder(self):
        return self._ensure_folder(self.get_input_folder(), 'weather')

    def get_database_construction_standards(self):
        """Returns the database of construction properties to be used by the archetypes-mapper. These are copied
        to the scenario if they are not yet present, based on the configured region for the scenario."""
        return os.path.join(self.get_databases_archetypes_folder(), 'CONSTRUCTION_STANDARD.xlsx')

    def get_database_use_types_properties(self):
        """Returns the database of construction properties to be used by the archetypes-mapper. These are copied
        to the scenario if they are not yet present, based on the configured region for the scenario."""
        return os.path.join(self.get_database_use_types_folder(), 'USE_TYPE_PROPERTIES.xlsx')

    def get_database_supply_assemblies(self):
        """Returns the database of supply components for cost analysis. These are copied
        to the scenario if they are not yet present, based on the configured region for the scenario."""
        return os.path.join(self.get_databases_assemblies_folder(), 'SUPPLY.xlsx')

    def get_database_supply_assemblies_new(self):
        """Returns the database of basic supply system compositions for stand-alone buildings in the energy system
        optimisation. """
        return os.path.join(self.get_databases_assemblies_folder(), 'SUPPLY_NEW.xlsx')

    def get_database_air_conditioning_systems(self):
        return os.path.join(self.get_databases_assemblies_folder(), 'HVAC.xlsx')

    def get_database_envelope_systems(self):
        """databases/Systems/envelope_systems.csv"""
        return os.path.join(self.get_databases_assemblies_folder(), 'ENVELOPE.xlsx')

    def get_database_conversion_systems(self):
        """Returns the database of supply components for cost analysis. These are copied
        to the scenario if they are not yet present, based on the configured region for the scenario."""
        return os.path.join(self.get_databases_folder(), 'components', 'CONVERSION.xlsx')

    def get_database_conversion_systems_new(self):
        """Returns the database of supply components for analysis of different objective functions. These are copied
        to the scenario if they are not yet present, based on the configured region for the scenario."""
        return os.path.join(self.get_databases_folder(), 'components', 'CONVERSION_NEW.xlsx')

    def get_database_conversion_systems_cold_thermal_storage_names(self):
        """Return the list of thermal storage tanks"""
        if not os.path.exists(self.get_database_conversion_systems()):
            return []
        import pandas as pd
        data = pd.read_excel(self.get_database_conversion_systems(), sheet_name="TES")
        data = data[data["type"] == "COOLING"]
        names = sorted(data["code"])
        return names

    def get_database_distribution_systems(self):
        """Returns the database of supply components for cost analysis. These are copied
        to the scenario if they are not yet present, based on the configured region for the scenario."""
        return os.path.join(self.get_databases_folder(), 'components', 'DISTRIBUTION.xlsx')

    def get_database_feedstocks(self):
        """Returns the database of supply components for cost analysis. These are copied
        to the scenario if they are not yet present, based on the configured region for the scenario."""
        return os.path.join(self.get_databases_folder(), 'components', 'FEEDSTOCKS.xlsx')

    def get_database_energy_carriers(self):
        """Returns the database of supply components for cost analysis. These are copied
        to the scenario if they are not yet present, based on the configured region for the scenario."""
        return os.path.join(self.get_databases_folder(), 'components', 'ENERGY_CARRIERS.xlsx')

    def get_building_geometry_folder(self):
        """scenario/inputs/building-geometry/"""
        return os.path.join(self.scenario, 'inputs', 'building-geometry')

    def get_building_properties_folder(self):
        """scenario/inputs/building-properties/"""
        return os.path.join(self.scenario, 'inputs', 'building-properties')

    def get_terrain_folder(self):
        return os.path.join(self.scenario, 'inputs', 'topography')

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

    # def get_zone_csv(self):
    #     """scenario/inputs/building-geometry/zone.csv"""
    #     zone_csv_path = os.path.join(self.get_building_geometry_folder(), 'zone.csv')
    #     check_cpg(zone_csv_path)
    #     return zone_csv_path

    # def get_zone_xlsx(self):
    #     """scenario/inputs/building-geometry/zone.xlsx"""
    #     zone_xlsx_path = os.path.join(self.get_building_geometry_folder(), 'zone.xlsx')
    #     check_cpg(zone_xlsx_path)
    #     return zone_xlsx_path

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
        from geopandas import GeoDataFrame as gdf
        zone_building_names = sorted(gdf.from_file(self.get_zone_geometry())['Name'].values)
        return zone_building_names

    def get_building_typology(self):
        """scenario/inputs/building-properties/typology.dbf"""
        return os.path.join(self.get_building_properties_folder(), 'typology.dbf')

    # def get_building_typology_csv(self):
    #     """scenario/inputs/building-properties/typology.csv"""
    #     return os.path.join(self.get_building_properties_folder(), 'typology.csv')

    # def get_building_typology_xlsx(self):
    #     """scenario/inputs/building-properties/typology.xlsx"""
    #     return os.path.join(self.get_building_properties_folder(), 'typology.xlsx')

    def get_building_supply(self):
        """scenario/inputs/building-properties/supply_systems.dbf"""
        return os.path.join(self.get_building_properties_folder(), 'supply_systems.dbf')

    def get_building_internal(self):
        """scenario/inputs/building-properties/internal_loads.dbf"""
        return os.path.join(self.get_building_properties_folder(), 'internal_loads.dbf')

    def get_building_comfort(self):
        """scenario/inputs/building-properties/indoor_comfort.dbf"""
        return os.path.join(self.get_building_properties_folder(), 'indoor_comfort.dbf')

    def get_building_air_conditioning(self):
        """scenario/inputs/building-properties/air_conditioning.dbf"""
        return os.path.join(self.get_building_properties_folder(), 'air_conditioning.dbf')

    def get_building_architecture(self):
        """scenario/inputs/building-properties/architecture.dbf
        This file is generated by the data-helper script.
        This file is used in the embodied energy script (cea/embodied.py)
        and the demand script (cea/demand_main.py)"""
        return os.path.join(self.get_building_properties_folder(), 'architecture.dbf')

    def get_building_weekly_schedules_folder(self):
        """scenario/inputs/building-properties/schedules/"""
        return self._ensure_folder(self.get_building_properties_folder(), 'schedules')

    def get_building_weekly_schedules(self, building):
        """
        scenario/inputs/building-properties/schedules/{building}.csv
        This file contains schedules of occupancy, appliance use, etc of each building.

        The format is a bit weird (e.g. not strictly a CSV table):

        First row contains two columns (METADATA, <schedule-type>
        Second row contains 13 columns (MONTHLY_MULTIPLIER, <jan-multiplier>, <feb-multiplier>, etc.)
        The following rows are three sets of HOUR 1-24, one set for each of DAY in {WEEKDAY, SATURDAY, SUNDAY}

        These weekly schedules are used by the schedule-maker script to create the schedules for each hour of the
        year (``get_schedule_model_file``).

        Do not read this file yourself, instead, use :py:func`cea.utilities.schedule_reader.read_cea_schedule`

        :param str building: The building to create the schedule for
        :return:
        """
        return os.path.join(self.get_building_weekly_schedules_folder(), '{}.csv'.format(building))

    def get_schedule_model_folder(self):
        """scenario/outputs/data/occupancy
        Folder to store occupancy schedules to.
        """
        return self._ensure_folder(self.scenario, 'outputs', 'data', 'occupancy')

    def get_schedule_model_file(self, building):
        """
        scenario/outputs/data/occupancy/{building}.csv

        This file contains schedules of occupancy, appliance use, etc of each building.
        Schedules are 8760 values per year
        :param building: The building to get the schedule file for.
        :return:
        """
        return os.path.join(self.get_schedule_model_folder(), '{}.csv'.format(building))

    def get_terrain(self):
        """scenario/inputs/topography/terrain.tif"""
        return os.path.join(self.get_terrain_folder(), 'terrain.tif')

    def get_input_network_folder(self, network_type, network_name=""):
        if network_name == '':  # in case there is no specific network name (default case)
            return self._ensure_folder(self.get_thermal_network_folder(), network_type)
        else:
            return self._ensure_folder(self.get_thermal_network_folder(), network_type, network_name)

    def get_network_layout_edges_shapefile(self, network_type, network_name=""):
        """scenario/outputs/thermal-network/DH or DC/edges.shp"""
        shapefile_path = os.path.join(self.get_input_network_folder(network_type, network_name), 'edges.shp')
        check_cpg(shapefile_path)
        return shapefile_path

    def get_network_layout_nodes_shapefile(self, network_type, network_name=""):
        """scenario/outputs/thermal-network/DH or DC/nodes.shp"""
        shapefile_path = os.path.join(self.get_input_network_folder(network_type, network_name), 'nodes.shp')
        check_cpg(shapefile_path)
        return shapefile_path

    # THERMAL NETWORK OUTPUTS
    def get_thermal_network_folder(self):
        return self._ensure_folder(self.scenario, 'outputs', 'data', 'thermal-network')

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
            return list(nodes_df[is_plant]['Name'].values)
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
        return self._ensure_folder(self.get_thermal_network_folder(), "reduced_timesteps")

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
        return self._ensure_folder(self.scenario, 'inputs', 'networks')

    def get_street_network(self):
        shapefile_path = os.path.join(self.get_networks_folder(), "streets.shp")
        check_cpg(shapefile_path)
        return shapefile_path

    # def get_streets_csv(self):
    #     """scenario/inputs/networks/streets.csv"""
    #     streets_csv_path = os.path.join(self.get_building_geometry_folder(), 'streets.csv')
    #     check_cpg(streets_csv_path)
    #     return streets_csv_path
    #
    # def get_streets_xlsx(self):
    #     """scenario/inputs/networks/streets.xlsx"""
    #     streets_xlsx_path = os.path.join(self.get_building_geometry_folder(), 'streets.xlsx')
    #     check_cpg(streets_xlsx_path)
    #     return streets_xlsx_path

    # OUTPUTS

    # SOLAR-RADIATION
    def get_solar_radiation_folder(self):
        """scenario/outputs/data/solar-radiation"""
        return self._ensure_folder(self.scenario, 'outputs', 'data', 'solar-radiation')

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
        """scenario/outputs/data/solar-radiation/{building}_geometrgy.csv"""
        return os.path.join(self.get_solar_radiation_folder(), 'buidling_materials.csv')

    def solar_potential_folder(self):
        return self._ensure_folder(self.scenario, 'outputs', 'data', 'potentials', 'solar')

    def PV_results(self, building):
        """scenario/outputs/data/potentials/solar/{building}_PV.csv"""
        return os.path.join(self.solar_potential_folder(), "{building}_PV.csv".format(building=building))

    def PV_totals(self, panel_type):
        """scenario/outputs/data/potentials/solar/{building}_PV_{panel_type}_total.csv.csv"""
        return os.path.join(self.solar_potential_folder(), "PV_{panel_type}_total.csv".format(panel_type=panel_type))

    def PV_total_buildings(self, panel_type):
        """scenario/outputs/data/potentials/solar/{building}_PV_{panel_type}_total_buildings.csv"""
        return os.path.join(self.solar_potential_folder(), 'PV_%s_total_buildings.csv' % panel_type)

    def PV_metadata_results(self, building):
        """scenario/outputs/data/potentials/solar/{building}_PV_sensors.csv"""
        return os.path.join(self.solar_potential_folder(), "{building}_PV_sensors.csv".format(building=building))

    def SC_results(self, building, panel_type):
        """scenario/outputs/data/potentials/solar/{building}_SC.csv"""
        return os.path.join(self.solar_potential_folder(), "{building}_SC_{panel_type}.csv".format(**locals()))

    def SC_totals(self, panel_type):
        """scenario/outputs/data/potentials/solar/{building}_PV.csv"""
        return os.path.join(self.solar_potential_folder(), "SC_{panel_type}_total.csv".format(panel_type=panel_type))

    def SC_total_buildings(self, panel_type):
        """scenario/outputs/data/potentials/solar/{building}_PV.csv"""
        return os.path.join(self.solar_potential_folder(), 'SC_%s_total_buildings.csv' % panel_type)

    def SC_metadata_results(self, building, panel_type):
        """scenario/outputs/data/potentials/solar/{building}_SC_sensors.csv"""
        return os.path.join(self.solar_potential_folder(), '%s_SC_%s_sensors.csv' % (building, panel_type))

    def PVT_results(self, building):
        """scenario/outputs/data/potentials/solar/{building}_SC.csv"""
        return os.path.join(self.solar_potential_folder(), '%s_PVT.csv' % building)

    def PVT_totals(self):
        """scenario/outputs/data/potentials/solar/{building}_PV.csv"""
        return os.path.join(self.solar_potential_folder(), 'PVT_total.csv')

    def PVT_total_buildings(self):
        """scenario/outputs/data/potentials/solar/{building}_PV.csv"""
        return os.path.join(self.solar_potential_folder(), 'PVT_total_buildings.csv')

    def PVT_metadata_results(self, building):
        """scenario/outputs/data/potentials/solar/{building}_SC_sensors.csv"""
        solar_potential_folder = os.path.join(self.scenario, 'outputs', 'data', 'potentials', 'solar')
        return os.path.join(solar_potential_folder, '%s_PVT_sensors.csv' % building)

    # DEMAND

    def get_demand_results_folder(self):
        """scenario/outputs/data/demand"""
        return self._ensure_folder(self.scenario, 'outputs', 'data', 'demand')

    def get_total_demand(self, format='csv'):
        """scenario/outputs/data/demand/Total_demand.csv"""
        return os.path.join(self.get_demand_results_folder(), 'Total_demand.%(format)s' % locals())

    def get_demand_results_file(self, building, format='csv'):
        """scenario/outputs/data/demand/{building}.csv"""
        return os.path.join(self.get_demand_results_folder(), '%(building)s.%(format)s' % locals())

    # EMISSIONS
    def get_lca_emissions_results_folder(self):
        """scenario/outputs/data/emissions"""
        lca_emissions_results_folder = os.path.join(self.scenario, 'outputs', 'data', 'emissions')
        if not os.path.exists(lca_emissions_results_folder):
            os.makedirs(lca_emissions_results_folder)
        return lca_emissions_results_folder

    def get_lca_embodied(self):
        """scenario/outputs/data/emissions/Total_LCA_embodied.csv"""
        return os.path.join(self.get_lca_emissions_results_folder(), 'Total_LCA_embodied.csv')

    def get_lca_operation(self):
        """scenario/outputs/data/emissions/Total_LCA_operation.csv"""
        return os.path.join(self.get_lca_emissions_results_folder(), 'Total_LCA_operation.csv')

    def get_lca_mobility(self):
        """scenario/outputs/data/emissions/Total_LCA_mobility.csv"""
        return os.path.join(self.get_lca_emissions_results_folder(), 'Total_LCA_mobility.csv')

    # COSTS
    def get_costs_folder(self):
        """scenario/outputs/data/costs"""
        return self._ensure_folder(self.scenario, 'outputs', 'data', 'costs')

    def get_multi_criteria_results_folder(self):
        """scenario/outputs/data/multi-criteria"""
        multi_criteria_results_folder = os.path.join(self.scenario, 'outputs', 'data', 'multicriteria')
        if not os.path.exists(multi_criteria_results_folder):
            os.makedirs(multi_criteria_results_folder)
        return multi_criteria_results_folder

    def get_multi_criteria_analysis(self, generation):
        return os.path.join(self.get_multi_criteria_results_folder(),
                            'gen_' + str(generation) + '_multi_criteria_analysis.csv')

    # RETROFIT POTENTIAL

    def get_costs_operation_file(self):
        """scenario/outputs/data/costs/{load}_cost_operation.pdf"""
        return os.path.join(self.get_costs_folder(), 'supply_system_costs_today.csv' % locals())

    # GRAPHS
    def get_plots_folder(self, category):
        """scenario/outputs/plots/timeseries"""
        return self._ensure_folder(self.scenario, 'outputs', 'plots', category)

    def get_timeseries_plots_file(self, building, category=''):
        """scenario/outputs/plots/timeseries/{building}.html
        :param category:
        """
        return os.path.join(self.get_plots_folder(category), '%(building)s.html' % locals())

    # OTHER
    def get_temporary_folder(self):
        """Temporary folder as returned by `tempfile`."""
        return self._temp_directory.name

    def get_temporary_file(self, filename):
        """Returns the path to a file in the temporary folder with the name `filename`"""
        return os.path.join(self.get_temporary_folder(), filename)


def check_cpg(shapefile_path):
    # ensures that the CPG file is the correct one
    if os.path.isfile(shapefile_path):
        from cea.utilities.standardize_coordinates import ensure_cpg_file
        ensure_cpg_file(shapefile_path)


class ReferenceCaseOpenLocator(InputLocator):
    """This is a special InputLocator that extracts the builtin reference case
    (``cea/examples/reference-case-open.zip``) to the temporary folder and uses the baseline scenario in there"""

    def __init__(self):
        temp_folder = tempfile.gettempdir()
        project_folder = os.path.join(temp_folder, 'reference-case-open')
        reference_case = os.path.join(project_folder, 'baseline')

        import cea.examples
        import zipfile
        archive = zipfile.ZipFile(os.path.join(os.path.dirname(cea.examples.__file__), 'reference-case-open.zip'))

        if os.path.exists(project_folder):
            shutil.rmtree(project_folder)
            assert not os.path.exists(project_folder), 'FAILED to remove %s' % project_folder

        archive.extractall(temp_folder)
        super(ReferenceCaseOpenLocator, self).__init__(scenario=reference_case)

    def get_default_weather(self):
        """The reference-case-open uses the Zug weather file..."""
        return self.get_weather('Zug-inducity_1990_2010_TMY')
