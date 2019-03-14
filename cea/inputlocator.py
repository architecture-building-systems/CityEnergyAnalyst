"""
inputlocator.py - locate input files by name based on the reference folder structure.
"""
import os
import shutil
import tempfile

import cea.config

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
    def __init__(self, scenario):
        self.scenario = scenario
        self.db_path = self.find_db_path()
        self.weather_path = os.path.join(self.db_path, 'weather')

    @staticmethod
    def find_db_path():
        """The path to the databases file is either a subfolder of the folder containing inputlocator.py
        (normal mode, part of the cea) or needs to be read from a file `databases.pth` (ArcGIS mode)"""
        db_path = os.path.join(os.path.dirname(__file__), 'databases')
        if os.path.exists(db_path):
            return db_path
        else:
            databases_pth = os.path.join(os.path.dirname(__file__), 'databases.pth')
            assert os.path.exists(databases_pth), 'File not found: %s' % databases_pth
            with open(databases_pth) as f:
                return f.read().strip()

    @staticmethod
    def _ensure_folder(*components):
        """Return the `*components` joined together as a path to a folder and ensure that that folder exists on disc.
        If it doesn't exist yet, attempt to make it with `os.makedirs`."""
        folder = os.path.join(*components)
        if not os.path.exists(folder):
            os.makedirs(folder)
        return folder

    def get_project_path(self):
        """Returns the parent folder of a scenario - this is called a project or 'case-study'"""
        return os.path.dirname(self.scenario)

    def get_input_folder(self):
        return os.path.join(self.scenario, "inputs")

    def get_optimization_results_folder(self):
        """scenario/outputs/data/optimization"""
        return self._ensure_folder(self.scenario, 'outputs', 'data', 'optimization')

    def get_optimization_master_results_folder(self):
        """scenario/outputs/data/optimization/master
        Master checkpoints
        """
        return self._ensure_folder(self.get_optimization_results_folder(), "master")

    def get_optimization_slave_results_folder(self, gen_num):
        """scenario/outputs/data/optimization/slave
        Slave results folder (storage + operation pattern)
        """
        return self._ensure_folder(self.get_optimization_results_folder(), "slave/gen_%(gen_num)s" % locals())

    def get_optimization_slave_storage_operation_data(self, ind_num, gen_num):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(gen_num),
                            'ind_%(ind_num)s_StorageOperationData.csv' % locals())

    def get_optimization_individuals_in_generation(self, gen_num):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(gen_num),
                            'generation_%(gen_num)s_individuals.csv' % locals())

    def get_optimization_all_individuals(self):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_results_folder(),
                            'slave/All_individuals.csv')

    def list_optimization_all_individuals(self):
        """Return a list of "scenario/generation/individual" strings for scenario comparisons"""
        import csv
        scenario = os.path.basename(self.scenario)
        all_individuals_csv = self.get_optimization_all_individuals()
        result = []
        if os.path.exists(all_individuals_csv):
            reader = csv.DictReader(open(all_individuals_csv))
            for row in reader:
                generation = int(float(row['generation']))
                individual = int(float(row['individual']))
                result.append('%(scenario)s/%(generation)i/ind%(individual)i' % locals())
        return result

    def get_optimization_slave_heating_activation_pattern(self, ind_num, gen_num):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(gen_num),
                            'ind_%(ind_num)s_Heating_Activation_Pattern.csv' % locals())

    def get_optimization_slave_cooling_activation_pattern(self, ind_num, gen_num):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(gen_num),
                            'ind_%(ind_num)s_Cooling_Activation_Pattern.csv' % locals())

    def get_optimization_slave_electricity_activation_pattern_heating(self, ind_num, gen_num):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(gen_num),
                            'ind_%(ind_num)s_Electricity_Activation_Pattern_Heating.csv' % locals())

    def get_optimization_slave_electricity_activation_pattern_cooling(self, ind_num, gen_num):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(gen_num),
                            'ind_%(ind_num)s_Electricity_Activation_Pattern_Cooling.csv' % locals())

    def get_optimization_slave_electricity_activation_pattern_processed(self, ind_num, gen_num):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_multi_criteria_results_folder(), 'gen' + str(gen_num) +
                            '_ind_%(ind_num)s_Electricity_Activation_Pattern_Processed.csv' % locals())

    def get_optimization_slave_natural_gas_imports(self, ind_num, gen_num):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(gen_num),
                            'ind_%(ind_num)s_Natural_Gas_Imports.csv' % locals())

    def get_optimization_slave_energy_mix_based_on_technologies(self, ind_num, gen_num, category):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_plots_folder(category), 'gen' + str(gen_num) +
                            '_ind_%(ind_num)s_yearly_energy_mix_based_on_technologies.csv' % locals())

    def get_address_of_individuals_of_a_generation(self, gen_num):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(gen_num), 'gen_' + str(gen_num) +
                            '_address_of_individuals.csv')

    def get_optimization_slave_cost_prime_primary_energy_data(self, ind_num, gen_num):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(gen_num),
                            'ind_%(ind_num)s_SlaveCostData.csv' % locals())

    def get_optimization_slave_slave_detailed_emission_and_eprim_data(self, ind_num, gen_num):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(gen_num),
                            'ind_%(ind_num)s_SlaveDetailedEmissionandEprimData.csv' % locals())

    def get_optimization_slave_investment_cost_detailed(self, ind_num, gen_num):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(gen_num),
                            'ind_%(ind_num)s_heating_InvestmentCostDetailed.csv' % locals())

    def get_optimization_slave_detailed_capacity_of_individual(self, ind_num, gen_num):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(gen_num),
                            'ind_%(ind_num)s_detailed_capacity.csv' % locals())

    def get_optimization_slave_investment_cost_detailed_cooling(self, ind_num, gen_num):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(gen_num),
                            'ind_%(ind_num)s_cooling_InvestmentCostDetailed.csv' % locals())

    def get_preprocessing_costs(self):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        self._ensure_folder(self.get_optimization_results_folder(), "slave")
        return os.path.join(self.get_optimization_results_folder(),
                            'slave/preprocessing_costs.csv')

    def get_optimization_slave_storage_flag(self, ind_num, gen_num):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(gen_num),
                            '%(configkey)s_StorageFlag.csv' % locals())

    def get_optimization_slave_storage_sizing_parameters(self, ind_num, gen_num):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(gen_num),
                            '%(configkey)s_Storage_Sizing_Parameters.csv' % locals())

    def get_optimization_decentralized_folder_disc_op_summary_cooling(self):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_decentralized_folder(), 'DiscOpSummary_cooling.csv')

    def get_optimization_decentralized_folder_disc_op_summary_heating(self):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_decentralized_folder(), 'DiscOpSummary_heating.csv')

    def get_optimization_decentralized_folder_building_result_cooling(self, buildingname, configuration):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""

        return os.path.join(self.get_optimization_decentralized_folder(),
                            buildingname + '_' + configuration + '_result_cooling.csv')

    def get_optimization_decentralized_folder_building_result_heating(self, buildingname):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_decentralized_folder(),
                            'DiscOp_' + buildingname + '_result_heating.csv')

    def get_optimization_network_results_summary(self, key):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_network_results_folder(),
                            'Network_summary_result_' + hex(int(str(key), 2)) + '.csv')

    def get_optimization_network_all_results_summary(self, key):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_network_results_folder(), 'Network_summary_result_' + key + '.csv')

    def get_optimization_network_totals_folder_total(self, indCombi):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_network_totals_folder(),
                            "Total_" + hex(int(str(indCombi), 2)) + ".csv")

    def get_optimization_network_results_folder(self):
        """scenario/outputs/data/optimization/network
        Network summary results
        """
        return self._ensure_folder(self.get_optimization_results_folder(), "network")

    def get_optimization_network_data_folder(self, network_data_file):
        """scenario/outputs/data/optimization/network
        Network summary results
        """
        return os.path.join(self.get_optimization_network_results_folder(), '%(network_data_file)s' % locals())

    def get_optimization_network_layout_folder(self):
        """scenario/outputs/data/optimization/network/layout
        Network layout files
        """
        return self._ensure_folder(self.get_optimization_network_results_folder(), "layout")

    def get_representative_week_optimization_network_layout_folder(self):
        """scenario/outputs/data/optimization/network/layout
        Network layout files
        """
        return self._ensure_folder(self.get_optimization_network_layout_folder(), "reduced_timesteps")

    def get_optimization_network_layout_costs_file(self, network_type):
        """scenario/outputs/data/optimization/network/layout/DC_costs.csv
        Optimized network layout files for pipes of district heating networks
        """
        return os.path.join(self.get_optimization_network_layout_folder(), "%s_costs.csv" % network_type)

    def get_optimization_network_layout_pipes_file(self, network_type):
        """scenario/outputs/data/optimization/network/layout/DH_PipesData.csv
        Optimized network layout files for pipes of district heating networks
        """
        return os.path.join(self.get_optimization_network_layout_folder(), "%s_AllEdges.csv" % network_type)

    def get_optimization_network_layout_nodes_file(self):
        """scenario/outputs/data/optimization/network/layout/DH_NodesData.csv
        Optimized network layout files for nodes of district heating networks
        """
        return os.path.join(self.get_optimization_network_layout_folder(), "NodesData_DH.csv")

    def get_optimization_network_edge_node_matrix_file(self, network_type, network_name):
        """scenario/outputs/data/optimization/network/layout/DH_EdgeNode.csv or DC_EdgeNode.csv
        Edge-node matrix for a heating or cooling network
        """
        return os.path.join(self.get_optimization_network_layout_folder(),
                            network_type + "_" + network_name + "_EdgeNode.csv")

    def get_optimization_network_node_list_file(self, network_type, network_name):
        """scenario/outputs/data/optimization/network/layout/DH_AllNodes.csv or DC_AllNodes.csv
        List of plant and consumer nodes in a district heating or cooling network and their building names
        """
        return os.path.join(self.get_optimization_network_layout_folder(),
                            network_type + "_" + network_name + "_Nodes.csv")

    def get_optimization_network_edge_list_file(self, network_type, network_name):
        """scenario/outputs/data/optimization/network/layout/DH_AllEdges.csv or DC_AllEdges.csv
        List of edges in a district heating or cooling network and their start and end nodes
        """
        return os.path.join(self.get_optimization_network_layout_folder(),
                            network_type + "_" + network_name + "_Edges.csv")

    def get_optimization_network_layout_massflow_file(self, network_type, network_name, representative_week=False):
        """scenario/outputs/data/optimization/network/layout/DH_MassFlow.csv or DC_MassFlow.csv
        Mass flow rates at each edge in a district heating or cooling network
        """
        if representative_week == True:
            folder = self.get_representative_week_optimization_network_layout_folder()
        else:
            folder = self.get_optimization_network_layout_folder()
        return os.path.join(folder, network_type + "_" + network_name + "_MassFlow_kgs.csv")

    def get_optimization_network_layout_supply_temperature_file(self, network_type, network_name,
                                                                representative_week=False):
        """scenario/outputs/data/optimization/network/layout/DH_T_Supply.csv or DC_T_Supply.csv
        Supply temperatures at each node for each time step for a district heating or cooling network
        """
        if representative_week == True:
            folder = self.get_representative_week_optimization_network_layout_folder()
        else:
            folder = self.get_optimization_network_layout_folder()
        return os.path.join(folder, network_type + "_" + network_name + "_T_Supply_K.csv")

    def get_optimization_network_generation_folder(self, generation):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return self._ensure_folder(self.get_optimization_network_results_folder(), str(generation))

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

    def get_optimization_network_layout_return_temperature_file(self, network_type, network_name,
                                                                representative_week=False):
        """scenario/outputs/data/optimization/network/layout/DH_T_Return.csv or DC_T_Return.csv
        Return temperatures at each node for each time step for a district heating or cooling network
        """
        if representative_week == True:
            folder = self.get_representative_week_optimization_network_layout_folder()
        else:
            folder = self.get_optimization_network_layout_folder()
        return os.path.join(folder, network_type + "_" + network_name + "_T_Return_K.csv")

    def get_optimization_network_substation_ploss_file(self, network_type, network_name, representative_week=False):
        """scenario/outputs/data/optimization/network/layout/DH_qloss_substations_kw.csv"""
        if representative_week == True:
            folder = self.get_representative_week_optimization_network_layout_folder()
        else:
            folder = self.get_optimization_network_layout_folder()
        return os.path.join(folder, network_type + "_" + network_name + "_ploss_Substations_kW.csv")

    def get_optimization_network_layout_qloss_system_file(self, network_type, network_name, representative_week=False):
        """scenario/outputs/data/optimization/network/layout/DH_qloss_System_kw.csv"""
        if representative_week == True:
            folder = self.get_representative_week_optimization_network_layout_folder()
        else:
            folder = self.get_optimization_network_layout_folder()
        return os.path.join(folder, network_type + "_" + network_name + "_qloss_System_kW.csv")

    def get_optimization_network_layout_ploss_system_edges_file(self, network_type, network_name,
                                                                representative_week=False):
        """scenario/outputs/data/optimization/network/layout/DH_qloss_System_kw.csv"""
        if representative_week == True:
            folder = self.get_representative_week_optimization_network_layout_folder()
        else:
            folder = self.get_optimization_network_layout_folder()
        return os.path.join(folder, network_type + "_" + network_name + "_ploss_System_edges_kW.csv")

    def get_optimization_network_layout_pressure_drop_file(self, network_type, network_name, representative_week=False):
        """scenario/outputs/data/optimization/network/layout/DH_P_DeltaP.csv or DC_P_DeltaP.csv
        Pressure drop over an entire district heating or cooling network at each time step
        """
        if representative_week == True:
            folder = self.get_representative_week_optimization_network_layout_folder()
        else:
            folder = self.get_optimization_network_layout_folder()
        return os.path.join(folder, network_type + "_" + network_name + "_P_DeltaP_Pa.csv")

    def get_optimization_network_layout_pressure_drop_kw_file(self, network_type, network_name,
                                                              representative_week=False):
        """scenario/outputs/data/optimization/network/layout/DH_P_DeltaP.csv or DC_P_DeltaP.csv
        Pressure drop over an entire district heating or cooling network at each time step
        """
        if representative_week == True:
            folder = self.get_representative_week_optimization_network_layout_folder()
        else:
            folder = self.get_optimization_network_layout_folder()
        return os.path.join(folder, network_type + "_" + network_name + "_P_DeltaP_kW.csv")

    def get_optimization_network_layout_plant_heat_requirement_file(self, network_type, network_name,
                                                                    representative_week=False):
        """scenario/outputs/data/optimization/network/layout/DH_Plant_heat_requirement.csv or DC_Plant_heat_requirement.csv
        Heat requirement at from the plants in a district heating or cooling network
        """
        if representative_week == True:
            folder = self.get_representative_week_optimization_network_layout_folder()
        else:
            folder = self.get_optimization_network_layout_folder()
        print (
            os.path.join(folder, network_type + "_" + network_name + "_Plant_heat_requirement_kW.csv"))  # todo: delete
        return os.path.join(folder, network_type + "_" + network_name + "_Plant_heat_requirement_kW.csv")

    def get_optimization_network_totals_folder(self):
        """scenario/outputs/data/optimization/network/totals
        Total files (inputs to substation + network in master)
        """
        return self._ensure_folder(self.get_optimization_network_results_folder(), "totals")

    def get_optimization_decentralized_folder(self):
        """scenario/outputs/data/optimization/decentralized
        Operation pattern for decentralized buildings"""
        return self._ensure_folder(self.get_optimization_results_folder(), "decentralized")

    def get_optimization_checkpoint(self, generation):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_master_results_folder(),
                            'CheckPoint_' + str(generation))

    def get_optimization_checkpoint_initial(self):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_master_results_folder(),
                            'CheckPoint_Initial')

    def get_optimization_checkpoint_final(self):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_master_results_folder(),
                            'Checkpoint_Final')

    def get_uncertainty_checkpoint(self, generation):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_uncertainty_results_folder(),
                            'CheckPoint_uncertainty_' + str(generation))

    def get_measurements(self):
        """scenario/inputs/
        Operation pattern for decentralized buildings"""
        return self._ensure_folder(self.scenario, 'inputs', 'building-metering', )

    def get_optimization_decentralized_result_file(self, building_name):
        """scenario/outputs/data/optimization/decentralized/DiscOp_${building_name}_result.csv"""
        return os.path.join(self.get_optimization_decentralized_folder(),
                            "DiscOp_%(building_name)s_result.csv" % locals())

    def get_optimization_substations_folder(self):
        """scenario/outputs/data/optimization/substations
        Substation results for decentralized buildings"""
        return self._ensure_folder(self.get_optimization_results_folder(), "substations")

    def get_optimization_substations_results_file(self, building_name):
        """scenario/outputs/data/optimization/substations/${building_name}_result.csv"""
        return os.path.join(self.get_optimization_substations_folder(), "%(building_name)s_result.csv" % locals())

    def get_optimization_substations_total_file(self, genome):
        """scenario/outputs/data/optimization/substations/Total_${genome}.csv"""
        return os.path.join(self.get_optimization_substations_folder(), "Total_%(genome)s.csv" % locals())

    def get_optimization_clustering_folder(self):
        """scenario/outputs/data/optimization/clustering_sax
        Clustering results for decentralized buildings"""
        return self._ensure_folder(self.get_optimization_results_folder(), "clustering_sax")

    # optimization
    def get_sewage_heat_potential(self):
        return os.path.join(self.get_potentials_folder(), "SWP.csv")

    def get_lake_potential(self):
        return os.path.join(self.get_potentials_folder(), "Lake_potential.csv")

    # POTENTIAL
    def get_potentials_folder(self):
        """scenario/outputs/data/potentials"""
        return self._ensure_folder(self.scenario, 'outputs', 'data', 'potentials')

    def get_potentials_solar_folder(self):
        """scenario/outputs/data/potentials/solar
        Contains raw solar files
        """
        return self._ensure_folder(self.get_potentials_folder(), "solar")

    def get_geothermal_potential(self):
        """scenario/outputs/data/potentials/geothermal/geothermal.csv"""
        return os.path.join(self.get_potentials_folder(), "geothermal", "geothermal.csv")

    def get_potentials_retrofit_folder(self):
        """scenario/outputs/data/potentials/retrofit.csv"""
        return self._ensure_folder(self.get_potentials_folder(), "retrofit")

    def get_retrofit_filters(self, name_retrofit):
        """scenario/outputs/data/potentials/retrofit.csv"""
        return os.path.join(self.get_potentials_retrofit_folder(), "potential_" + name_retrofit + ".csv")

    # DATABASES
    # FIXME: remove get_default_weather (use config instead)
    def get_default_weather(self):
        """weather/Zug-2010.epw
        path to database of archetypes file Archetypes_properties.xlsx"""
        import cea.config
        config = cea.config.Configuration()
        if not os.path.exists(config.weather):
            if config.weather in self.get_weather_names():
                return self.get_weather(config.weather)
            else:
                return self.get_weather(self.get_weather_names()[0])
        return config.weather

    def get_weather(self, name):
        """weather/{name}.epw Returns the path to a weather file with the name ``name``. This can either be one
        of the pre-configured weather files (see ``get_weather_names``) or a path to an existing weather file.
        Returns the default weather file if no other file can be resolved."""
        if not name:
            return self.get_default_weather()
        if os.path.exists(name) and name.endswith('.epw'):
            return name
        weather_file = os.path.join(self.weather_path, name + '.epw')
        if not os.path.exists(weather_file):
            return self.get_default_weather()
        return weather_file

    def get_weather_names(self):
        """Return a list of all installed epw files in the system"""
        weather_names = [os.path.splitext(f)[0] for f in os.listdir(self.weather_path)]
        return weather_names

    def get_weather_dict(self):
        """Return a dictionary with weather_name -> weather_path for the builtin weather files"""
        return {name: self.get_weather(name) for name in self.get_weather_names()}

    def get_weather_folder(self):
        return self._ensure_folder(self.get_input_folder(), 'weather')

    def _get_region_specific_db_file(self, region, folder, filename):
        """Copy a region-specific file from the database to a scenario, overwriting any existing one
        if it doesn't exist there yet and return the full path to the copy"""
        result_folder = self._ensure_folder(self.scenario, 'databases', region, folder)
        result_file = os.path.join(result_folder, filename)

        # copy it from the database, overwriting the existing file
        if not os.path.exists(result_file):
            if region == 'custom':
                raise cea.CustomDatabaseNotFound('Custom database not found: %(result_file)s' % locals())

            shutil.copyfile(os.path.join(self.db_path, region, folder, filename), result_file)

        return result_file

    def get_archetypes_properties(self, region):
        """Returns the database of construction properties to be used by the data-helper. These are copied
        to the scenario if they are not yet present, based on the configured region for the scenario."""
        return self._get_region_specific_db_file(region, 'archetypes', 'construction_properties.xlsx')

    def get_archetypes_schedules(self, region):
        """Returns the database of schedules to be used by the data-helper. These are copied
        to the scenario if they are not yet present, based on the configured region for the scenario."""
        return self._get_region_specific_db_file(region, 'archetypes', 'occupancy_schedules.xlsx')

    def get_archetypes_system_controls(self, region):
        """ Returns the database of region-specific system control parameters. These are copied
        to the scenario if they are not yet present, based on the configured region for the scenario.

        :param region:
        :return:
        """
        return self._get_region_specific_db_file(region, 'archetypes', 'system_controls.xlsx')

    def get_supply_systems(self, region):
        """Returns the database of supply systems for cost analysis. These are copied
        to the scenario if they are not yet present, based on the configured region for the scenario."""
        return self._get_region_specific_db_file(region, 'systems', 'supply_systems.xls')

    def get_life_cycle_inventory_supply_systems(self, region):
        """Returns the database of life cycle inventory for supply systems. These are copied
        to the scenario if they are not yet present, based on the configured region for the scenario."""
        return self._get_region_specific_db_file(region, 'lifecycle', 'LCA_infrastructure.xlsx')

    def get_electricity_costs(self, region):
        """Returns the database of life cycle inventory for supply systems. These are copied
        to the scenario if they are not yet present, based on the configured region for the scenario."""
        return self._get_region_specific_db_file(region, 'systems', 'electricity_costs.xlsx')

    def get_life_cycle_inventory_building_systems(self, region):
        """Returns the database of life cycle inventory for buildings systems. These are copied
        to the scenario if they are not yet present, based on the configured region for the scenario."""
        return self._get_region_specific_db_file(region, 'lifecycle', 'LCA_buildings.xlsx')

    def get_technical_emission_systems(self, region):
        """databases/Systems/emission_systems.csv"""
        return self._get_region_specific_db_file(region, 'systems', 'emission_systems.xls')

    def get_envelope_systems(self, region):
        """databases/Systems/emission_systems.csv"""
        return self._get_region_specific_db_file(region, 'systems', 'envelope_systems.xls')

    def get_thermal_networks(self, region):
        """db/Systems/thermal_networks.xls"""
        return self._get_region_specific_db_file(region, 'systems', 'thermal_networks.xls')

    def get_electrical_networks(self, region):
        """db/Systems/electrical_networks.xls"""
        return self._get_region_specific_db_file(region, 'systems', 'electrical_networks.xls')

    def get_data_benchmark(self, region):
        """Returns the database of life cycle inventory for supply systems. These are copied
        to the scenario if they are not yet present, based on the configured region for the scenario."""
        return self._get_region_specific_db_file(region, 'benchmarks', 'benchmark_2000W.xls')

    def get_uncertainty_db(self, region):
        """databases/CH/Uncertainty/uncertainty_distributions.xls"""
        return self._get_region_specific_db_file(region, 'uncertainty', 'uncertainty_distributions.xls')

    def get_uncertainty_results_folder(self):
        return self._ensure_folder(self.scenario, 'outputs', 'data', 'uncertainty')

    # INPUTS

    def get_building_geometry_folder(self):
        """scenario/inputs/building-geometry/"""
        return self._ensure_folder(self.scenario, 'inputs', 'building-geometry')

    def get_building_properties_folder(self):
        """scenario/inputs/building-geometry/"""
        return self._ensure_folder(self.scenario, 'inputs', 'building-properties')

    def get_terrain_folder(self):
        return self._ensure_folder(self.scenario, 'inputs', 'topography')

    def get_zone_geometry(self):
        """scenario/inputs/building-geometry/zone.shp"""
        shapefile_path = os.path.join(self.get_building_geometry_folder(), 'zone.shp')
        self.check_cpg(shapefile_path)
        return shapefile_path

    def get_district_geometry(self):
        """scenario/inputs/building-geometry/district.shp"""
        shapefile_path = os.path.join(self.get_building_geometry_folder(), 'district.shp')
        self.check_cpg(shapefile_path)
        return shapefile_path

    def check_cpg(self, shapefile_path):
        # ensures that the CPG file is the correct one
        from cea.utilities.standardize_coordinates import ensure_cpg_file
        ensure_cpg_file(shapefile_path)

    def get_zone_building_names(self):
        """Return the list of buildings in the Zone"""
        if not os.path.exists(self.get_zone_geometry()):
            return []
        from geopandas import GeoDataFrame as gdf
        zone_building_names = sorted(gdf.from_file(self.get_zone_geometry())['Name'].values)
        return [b.encode('utf-8') for b in zone_building_names]

    def get_building_geometry_citygml(self):
        """scenario/outputs/data/solar-radiation/district.gml"""
        return os.path.join(self.get_solar_radiation_folder(), 'district.gml')

    def get_building_age(self):
        """scenario/inputs/building-properties/age.dbf"""
        return os.path.join(self.get_building_properties_folder(), 'age.dbf')

    def get_building_occupancy(self):
        """scenario/inputs/building-properties/building_occupancy.dbf"""
        return os.path.join(self.get_building_properties_folder(), 'occupancy.dbf')

    def get_building_supply(self):
        """scenario/inputs/building-properties/building_supply.dbf"""
        return os.path.join(self.get_building_properties_folder(), 'supply_systems.dbf')

    def get_building_internal(self):
        """scenario/inputs/building-properties/internal_loads.dbf"""
        return os.path.join(self.get_building_properties_folder(), 'internal_loads.dbf')

    def get_building_comfort(self):
        """scenario/inputs/building-properties/indoor_comfort.dbf"""
        return os.path.join(self.get_building_properties_folder(), 'indoor_comfort.dbf')

    def get_building_hvac(self):
        """scenario/inputs/building-properties/technical_systems.dbf"""
        return os.path.join(self.get_building_properties_folder(), 'technical_systems.dbf')

    def get_building_restrictions(self):
        """scenario/inputs/building-properties/technical_systems.dbf"""
        return os.path.join(self.get_building_properties_folder(), 'restrictions.dbf')

    def get_building_architecture(self):
        """scenario/inputs/building-properties/architecture.dbf
        This file is generated by the properties script.
        This file is used in the embodied energy script (cea/embodied.py)
        and the demand script (cea/demand_main.py)"""
        return os.path.join(self.get_building_properties_folder(), 'architecture.dbf')

    def get_building_overrides(self):
        """scenario/inputs/building-properties/overrides.csv
        This file contains overrides to the building properties input files. They are applied after reading
        those files and are matched by column name.
        """
        return os.path.join(self.get_building_properties_folder(), 'overrides.csv')

    def get_terrain(self):
        """scenario/inputs/topography/terrain.tif"""
        return os.path.join(self.get_terrain_folder(), 'terrain.tif')

    def get_input_network_folder(self, network_type, network_name):
        if network_name == '':  # in case there is no specfici networ name (default case)
            return self._ensure_folder(self.scenario, 'inputs', 'networks', network_type)
        else:
            return self._ensure_folder(self.scenario, 'inputs', 'networks', network_type, network_name)

    def get_network_layout_edges_shapefile(self, network_type, network_name):
        """scenario/inputs/network/DH or DC/network-edges.shp"""
        shapefile_path = os.path.join(self.get_input_network_folder(network_type, network_name), 'edges.shp')
        self.check_cpg(shapefile_path)
        return shapefile_path

    def get_network_layout_nodes_shapefile(self, network_type, network_name):
        """scenario/inputs/network/DH or DC/network-nodes.shp"""
        shapefile_path = os.path.join(self.get_input_network_folder(network_type, network_name), 'nodes.shp')
        self.check_cpg(shapefile_path)
        return shapefile_path

    def get_network_layout_pipes_csv_file(self, network):
        """scenario/outputs/data/optimization/network/layout/DH_PipesData.csv or DC_PipesData.csv
        Network layout files for pipes of district heating or cooling networks
        """
        return os.path.join(self.get_optimization_network_layout_folder(), "PipesData_" + network + ".csv")

    def get_network_layout_nodes_csv_file(self, network):
        """scenario/outputs/data/optimization/network/layout/DH_NodesData.csv or DC_NodesData.csv
        Network layout files for nodes of district heating or cooling networks
        """
        return os.path.join(self.get_optimization_network_layout_folder(), "NodesData_" + network + ".csv")

    def get_network_node_types_csv_file(self, network_type, network_name):
        """scenario/outputs/data/optimization/network/layout/DH_Nodes.csv or DC_NodesData.csv
        Network layout files for nodes of district heating or cooling networks
        """
        return os.path.join(self.get_optimization_network_layout_folder(),
                            network_type + '_' + network_name + '_Nodes.csv')

    def get_edge_mass_flow_csv_file(self, network_type, network_name):
        """scenario/outputs/data/optimization/network/layout/DH_NodesData.csv or DC_NodesData.csv
        Network layout files for nodes of district heating or cooling networks
        """
        return os.path.join(self.get_optimization_network_layout_folder(), 'Nominal_EdgeMassFlow_at_design_' +
                            network_type + '_' + network_name + '_kgpers.csv')

    def get_node_mass_flow_csv_file(self, network_type, network_name):
        """scenario/outputs/data/optimization/network/layout/DH_NodesData.csv or DC_NodesData.csv
        Network layout files for nodes of district heating or cooling networks
        """
        return os.path.join(self.get_optimization_network_layout_folder(), 'Nominal_NodeMassFlow_at_design_' +
                            network_type + '_' + network_name + '_kgpers.csv')

    def get_thermal_demand_csv_file(self, network_type, network_name):
        """scenario/outputs/data/optimization/network/layout/DH_NodesData.csv or DC_NodesData.csv
        Network layout files for nodes of district heating or cooling networks
        """
        return os.path.join(self.get_optimization_network_layout_folder(), 'Aggregated_Demand_' +
                            network_type + '_' + network_name + '_Wh.csv')

    def get_daysim_mat(self):
        """this gets the file that documents all of the radiance/default_materials"""
        return os.path.join(self.get_solar_radiation_folder(), 'materials.rad')

    def get_network_street_folder(self):
        return self._ensure_folder(self.scenario, 'inputs', 'networks')

    def get_street_network(self):
        shapefile_path = os.path.join(self.get_network_street_folder(), "streets.shp")
        self.check_cpg(shapefile_path)
        return shapefile_path

    def get_minimum_spanning_tree(self):
        shapefile_path = os.path.join(self.get_network_street_folder(), "mst_network.shp")
        self.check_cpg(shapefile_path)
        return shapefile_path

    # OUTPUTS

    # SOLAR-RADIATION
    def get_radiation(self):  # todo: delete if not used
        """scenario/outputs/data/solar-radiation/radiation.csv"""
        return os.path.join(self._ensure_folder(self.get_solar_radiation_folder()), 'radiation.csv')

    def get_solar_radiation_folder(self):
        """scenario/outputs/data/solar-radiation"""
        return self._ensure_folder(self.scenario, 'outputs', 'data', 'solar-radiation')

    def get_radiation_building(self, building_name):
        """scenario/outputs/data/solar-radiation/${building_name}_insolation_Whm2.json"""
        return os.path.join(self.get_solar_radiation_folder(), '%s_insolation_Whm2.json' % building_name)

    def get_radiation_metadata(self, building_name):
        """scenario/outputs/data/solar-radiation/{building_name}_geometrgy.csv"""
        return os.path.join(self.get_solar_radiation_folder(), '%s_geometry.csv' % building_name)

    def get_building_list(self):
        """scenario/outputs/data/solar-radiation/radiation.csv"""
        solar_radiation_folder = os.path.join(self.scenario, 'outputs', 'data', 'solar-radiation')
        return os.path.join(solar_radiation_folder, 'radiation.csv')

    def get_3D_geometry_folder(self):
        """scenario/inputs/3D-geometries"""
        return self._ensure_folder(os.path.join(self.scenario, 'inputs', '3D-geometries'))

    def get_surface_properties(self):
        """scenario/outputs/data/solar-radiation/properties_surfaces.csv"""
        return os.path.join(self.get_solar_radiation_folder(), 'properties_surfaces.csv')

    def get_sensitivity_output(self, method, samples):
        """scenario/outputs/data/sensitivity-analysis/sensitivity_${METHOD}_${SAMPLES}.xls"""
        return os.path.join(self.scenario, 'outputs', 'data', 'sensitivity-analysis',
                            'sensitivity_%(method)s_%(samples)s.xls' % locals())

    def get_sensitivity_plots_file(self, parameter):
        """scenario/outputs/plots/sensitivity/${PARAMETER}.pdf"""
        return os.path.join(self.scenario, 'outputs', 'plots', 'sensitivity', '%s.pdf' % parameter)

    ## POTENTIALS #FIXME: find better placement for these two locators

    def solar_potential_folder(self):
        return self._ensure_folder(self.scenario, 'outputs', 'data', 'potentials', 'solar')

    def PV_results(self, building_name):
        """scenario/outputs/data/potentials/solar/{building_name}_PV.csv"""
        return os.path.join(self.solar_potential_folder(), '%s_PV.csv' % building_name)

    def radiation_results(self, building_name):
        """scenario/outputs/data/potentials/solar/{building_name}_PV.csv"""
        return os.path.join(self.solar_potential_folder(), '%s_radiation.csv' % building_name)

    def PV_totals(self):
        """scenario/outputs/data/potentials/solar/{building_name}_PV.csv"""
        return os.path.join(self.solar_potential_folder(), 'PV_total.csv')

    def PV_total_buildings(self):
        """scenario/outputs/data/potentials/solar/{building_name}_PV.csv"""
        return os.path.join(self.solar_potential_folder(), 'PV_total_buildings.csv')

    def PV_network(self, network):
        """scenario/outputs/data/potentials/solar/{building_name}_PV.csv"""
        return os.path.join(self.solar_potential_folder(), 'PV_total_%s.csv' % network)

    def PV_metadata_results(self, building_name):
        """scenario/outputs/data/potentials/solar/{building_name}_PV_sensors.csv"""
        solar_potential_folder = os.path.join(self.scenario, 'outputs', 'data', 'potentials', 'solar')
        return os.path.join(solar_potential_folder, '%s_PV_sensors.csv' % building_name)

    def SC_results(self, building_name, panel_type):
        """scenario/outputs/data/potentials/solar/{building_name}_SC.csv"""
        return os.path.join(self.solar_potential_folder(), '%s_SC_%s.csv' % (building_name, panel_type))

    def SC_totals(self, panel_type):
        """scenario/outputs/data/potentials/solar/{building_name}_PV.csv"""
        return os.path.join(self.solar_potential_folder(), 'SC_%s_total.csv' % panel_type)

    def SC_total_buildings(self, panel_type):
        """scenario/outputs/data/potentials/solar/{building_name}_PV.csv"""
        return os.path.join(self.solar_potential_folder(), 'SC_%s_total_buildings.csv' % panel_type)

    def SC_metadata_results(self, building_name, panel_type):
        """scenario/outputs/data/potentials/solar/{building_name}_SC_sensors.csv"""
        return os.path.join(self.solar_potential_folder(), '%s_SC_%s_sensors.csv' % (building_name, panel_type))

    def PVT_results(self, building_name):
        """scenario/outputs/data/potentials/solar/{building_name}_SC.csv"""
        return os.path.join(self.solar_potential_folder(), '%s_PVT.csv' % building_name)

    def PVT_totals(self):
        """scenario/outputs/data/potentials/solar/{building_name}_PV.csv"""
        return os.path.join(self.solar_potential_folder(), 'PVT_total.csv')

    def PVT_total_buildings(self):
        """scenario/outputs/data/potentials/solar/{building_name}_PV.csv"""
        return os.path.join(self.solar_potential_folder(), 'PVT_total_buildings.csv')

    def PVT_metadata_results(self, building_name):
        """scenario/outputs/data/potentials/solar/{building_name}_SC_sensors.csv"""
        solar_potential_folder = os.path.join(self.scenario, 'outputs', 'data', 'potentials', 'solar')
        return os.path.join(solar_potential_folder, '%s_PVT_sensors.csv' % building_name)

    # DEMAND

    def get_demand_results_folder(self):
        """scenario/outputs/data/demand"""
        return self._ensure_folder(self.scenario, 'outputs', 'data', 'demand')

    def get_total_demand(self, format='csv'):
        """scenario/outputs/data/demand/Total_demand.csv"""
        return os.path.join(self.get_demand_results_folder(), 'Total_demand.%(format)s' % locals())

    def get_demand_results_file(self, building_name, format='csv'):
        """scenario/outputs/data/demand/{building_name}.csv"""
        return os.path.join(self.get_demand_results_folder(), '%(building_name)s.%(format)s' % locals())

    def get_predefined_hourly_setpoints_folder(self, type_of_district_network):
        return self._ensure_folder(self.scenario, 'inputs', 'predefined-hourly-setpoints', str(type_of_district_network))

    def get_predefined_hourly_setpoints(self, building_name, type_of_district_network):
        """scenario/outputs/data/demand/{building_name}_.csv"""
        return os.path.join(self.get_predefined_hourly_setpoints_folder(type_of_district_network),  str(building_name) + '_temperature.csv')

    # THERMAL NETWORK

    def get_qloss(self, network_name, network_type, format='csv'):
        """scenario/outputs/data/optimization/network/layout/DH__P_Delta_P_Pa.csv"""
        return os.path.join(self.get_optimization_network_layout_folder(),
                            str(network_type) + '_' + str(network_name) + '_qloss_System_kW.%(format)s' % locals())

    def get_substation_HEX_cost(self, network_name, network_type, format='csv'):
        """scenario/outputs/data/optimization/network/layout/DH__substaion_HEX_cost.csv"""
        return os.path.join(self.get_optimization_network_layout_folder(),
                            str(network_type) + '_' + str(
                                network_name) + '_substaion_HEX_cost_USD.%(format)s' % locals())

    def get_ploss(self, network_name, network_type, format='csv'):
        """scenario/outputs/data/optimization/network/layout/DH__P_Delta_P_Pa.csv"""
        return os.path.join(self.get_optimization_network_layout_folder(),
                            str(network_type) + '_' + str(network_name) + '_P_DeltaP_kW.%(format)s' % locals())

    def get_qplant(self, network_name, network_type, format='csv'):
        """scenario/outputs/data/optimization/network/layout/DH__Plant_heat_requirement_kW.csv"""
        return os.path.join(self.get_optimization_network_layout_folder(),
                            str(network_type) + '_' + str(
                                network_name) + '_Plant_heat_requirement_kW.%(format)s' % locals())

    def get_pnode_s(self, network_name, network_type, format='csv'):
        """scenario/outputs/data/optimization/network/layout/DH__P_Supply_Pa.csv"""
        return os.path.join(self.get_optimization_network_layout_folder(),
                            str(network_type) + '_' + str(network_name) + '_P_Supply_Pa.%(format)s' % locals())

    def get_pnode_r(self, network_name, network_type, format='csv'):
        """scenario/outputs/data/optimization/network/layout/DC__P_Return_Pa.csv"""
        return os.path.join(self.get_optimization_network_layout_folder(),
                            str(network_type) + '_' + str(network_name) + '_P_Return_Pa.%(format)s' % locals())

    def get_Tnode_s(self, network_name, network_type, format='csv'):
        """scenario/outputs/data/optimization/network/layout/DH__T_Supply_K.csv"""
        return os.path.join(self.get_optimization_network_layout_folder(),
                            str(network_type) + '_' + str(network_name) + '_T_Supply_K.%(format)s' % locals())

    def get_Tnode_r(self, network_name, network_type, format='csv'):
        """scenario/outputs/data/optimization/network/layout/DC__T_Return_K.csv"""
        return os.path.join(self.get_optimization_network_layout_folder(),
                            str(network_type) + '_' + str(network_name) + '_T_Return_K.%(format)s' % locals())

    # CALIBRATION
    def get_calibration_folder(self):
        """scenario/outputs/data/calibration"""
        return self._ensure_folder(self.scenario, 'outputs', 'data', 'calibration')

    def get_calibration_problem(self, building_name, building_load):
        """scenario/outputs/data/calibration"""
        return os.path.join(self.get_calibration_folder(), 'problem_%(building_name)s_%(building_load)s.pkl' % locals())

    def get_calibration_gaussian_emulator(self, building_name, building_load):
        """scenario/outputs/data/calibration"""
        return os.path.join(self.get_calibration_folder(),
                            'emulator_%(building_name)s_%(building_load)s.pkl' % locals())

    def get_calibration_posteriors(self, building_name, building_load):
        """scenario/outputs/data/calibration"""
        return os.path.join(self.get_calibration_folder(),
                            'posteriors_%(building_name)s_%(building_load)s.csv' % locals())

    def get_calibration_clustering_folder(self):
        """scenario/outputs/data/calibration"""
        return self._ensure_folder(self.get_calibration_folder(), 'clustering')

    def get_calibration_clustering_clusters_folder(self):
        """scenario/outputs/data/calibration"""
        return self._ensure_folder(self.get_calibration_clustering_folder(), 'clusters')

    def get_demand_measured_folder(self):
        """scenario/outputs/data/demand"""
        return self._ensure_folder(self.scenario, 'inputs', 'building-metering')

    def get_demand_measured_file(self, building_name):
        """scenario/outputs/data/demand/{building_name}.csv"""
        return os.path.join(self.get_demand_measured_folder(), '%s.csv' % building_name)

    def get_calibration_cluster(self, sax_name):
        """scenario/outputs/data/demand/{sax_name}.csv"""
        return os.path.join(self.get_calibration_clustering_clusters_folder(), '%s.csv' % sax_name)

    def get_calibration_cluster_opt_checkpoint_folder(self):
        return self._ensure_folder(self.get_calibration_clustering_folder(), 'checkpoint')

    def get_calibration_cluster_opt_checkpoint(self, generation, building):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        file = self.get_calibration_folder()
        return os.path.join(self.get_calibration_cluster_opt_checkpoint_folder(),
                            'cp_gen_' + str(generation) + '_building_' + building)

    def get_calibration_cluster_mcda_folder(self):
        return self._ensure_folder(self.get_calibration_clustering_folder(), "multicriteria")

    def get_calibration_cluster_mcda(self, generation):
        return os.path.join(self.get_calibration_cluster_mcda_folder(), "mcda_gen_" + str(generation) + ".csv")

    def get_calibration_clusters_names(self):
        """scenario/outputs/data/demand/{sax_name}.csv"""
        return os.path.join(self.get_calibration_clustering_clusters_folder(), 'sax_names.csv')

    def get_calibration_clustering_plots_folder(self):
        return self._ensure_folder(self.get_calibration_clustering_folder(), "plots")

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
    def get_costs_folder(self):
        """scenario/outputs/data/costs"""
        return self._ensure_folder(self.scenario, 'outputs', 'data', 'costs')

    def get_costs_operation_file(self):
        """scenario/outputs/data/costs/{load}_cost_operation.pdf"""
        return os.path.join(self.get_costs_folder(), 'operation_costs.csv' % locals())

    # GRAPHS
    def get_plots_folder(self, category):
        """scenario/outputs/plots/timeseries"""
        return self._ensure_folder(self.scenario, 'outputs', 'plots', category)

    def get_4D_demand_plot(self, period):
        """scenario/outputs/plots/timeseries"""
        return os.path.join(self.get_plots_folder('4D_plots'),
                            'Demand_4D_plot_' + str(period[0]) + '_' + str(period[1]) + '.dbf')

    def get_4D_radiation_plot(self, period):
        """scenario/outputs/plots/timeseries"""
        return os.path.join(self.get_plots_folder('4D_plots'),
                            'Radiation_4D_plot_' + str(period[0]) + '_' + str(period[1]) + '.dbf')

    def get_4D_pv_plot(self, period):
        """scenario/outputs/plots/timeseries"""
        return os.path.join(self.get_plots_folder('4D_plots'),
                            'PV_4D_plot_' + str(period[0]) + '_' + str(period[1]) + '.dbf')

    def get_4D_pvt_plot(self, period):
        """scenario/outputs/plots/timeseries"""
        return os.path.join(self.get_plots_folder('4D_plots'),
                            'PVT_4D_plot_' + str(period[0]) + '_' + str(period[1]) + '.dbf')

    def get_4D_sc_plot(self, period):
        """scenario/outputs/plots/timeseries"""
        return os.path.join(self.get_plots_folder('4D_plots'),
                            'SC_4D_plot_' + str(period[0]) + '_' + str(period[1]) + '.dbf')

    def get_timeseries_plots_file(self, building_name, category=''):
        """scenario/outputs/plots/timeseries/{building_name}.html
        :param category:
        """
        return os.path.join(self.get_plots_folder(category), '%(building_name)s.html' % locals())

    def get_networks_plots_file(self, network_name, category):
        """scenario/outputs/plots/timeseries/{network_name}.html"""
        return os.path.join(self.get_plots_folder(category), '%(network_name)s.png' % locals())

    def get_benchmark_plots_file(self):
        """scenario/outputs/plots/graphs/Benchmark_scenarios.pdf"""
        return os.path.join(self.get_plots_folder(''), 'Benchmark_scenarios.pdf')

    # OTHER
    def get_temporary_folder(self):
        """Temporary folder as returned by `tempfile`."""
        return tempfile.gettempdir()

    def get_temporary_file(self, filename):
        """Returns the path to a file in the temporary folder with the name `filename`"""
        return os.path.join(self.get_temporary_folder(), filename)

    def get_surrogate_folder(self):
        """scenario/outputs/data/surrogate"""
        return self._ensure_folder(self.scenario, 'outputs', 'surrogate_model')

    def get_nn_inout_folder(self):
        """scenario/outputs/data/surrogate"""
        return self._ensure_folder(self.scenario, 'outputs', 'surrogate_model', 'inputs_outputs')

    def get_neural_network_folder(self):
        """scenario/outputs/data/surrogate/neural_network_folder"""
        return self._ensure_folder(self.scenario, 'outputs', 'surrogate_model', 'neural_network')

    def get_minmaxscaler_folder(self):
        """scenario/outputs/data/surrogate/neural_network_folder"""
        return self._ensure_folder(self.scenario, 'outputs', 'surrogate_model', 'minmaxscalar')

    def get_neural_network_model(self):
        """scenario/outputs/data/surrogate/neural_network_folder"""
        structure = os.path.join(self.get_neural_network_folder(), 'nn_structure.json')
        matrix = os.path.join(self.get_neural_network_folder(), 'nn_matrix.h5')
        return structure, matrix

    def get_neural_network_resume(self):
        """scenario/outputs/data/surrogate/neural_network_folder"""
        model_resume = os.path.join(self.get_neural_network_folder(), 'model_resume.h5')
        return model_resume

    def get_minmaxscalar_model(self):
        """scenario/outputs/data/surrogate/neural_network_folder"""
        scalerX_file = os.path.join(self.get_neural_network_folder(), 'scalerX.save')
        scalerT_file = os.path.join(self.get_neural_network_folder(), 'scalerT.save')
        return scalerX_file, scalerT_file

    def get_neural_network_estimates(self):
        """scenario/outputs/data/surrogate/neural_network_folder"""
        return os.path.join(self.get_neural_network_folder(), 'model_estimates.csv')

    def get_result_building_NN(self, name):
        """scenario/outputs/data/surrogate/neural_network_folder"""
        return os.path.join(self.get_neural_network_folder(), name + '.csv')

    def are_equal(self, path_a, path_b):
        """Checks to see if two paths are equal"""
        path_a = os.path.normcase(os.path.normpath(os.path.realpath(os.path.abspath(path_a))))
        path_b = os.path.normcase(os.path.normpath(os.path.realpath(os.path.abspath(path_b))))
        return path_a == path_b

    # MPC by Concept Project
    def get_mpc_results_folder(self, output_folder="mpc-building"):
        """scenario/outputs/data/optimization"""
        return self._ensure_folder(self.scenario, 'outputs', 'data', output_folder)

    def get_mpc_results_outputs(self, building, output_folder):
        """scenario/outputs/data/optimization"""
        return os.path.join(self.get_mpc_results_folder(output_folder), building + '_outputs.csv')

    def get_mpc_results_controls(self, building, output_folder):
        """scenario/outputs/data/optimization"""
        return os.path.join(self.get_mpc_results_folder(output_folder), building + '_controls.csv')

    def get_mpc_results_states(self, building, output_folder):
        """scenario/outputs/data/optimization"""
        return os.path.join(self.get_mpc_results_folder(output_folder), building + '_states.csv')

    def get_mpc_results_min_outputs(self, building, output_folder):
        """scenario/outputs/data/optimization"""
        return os.path.join(self.get_mpc_results_folder(output_folder), building + '_outputs_minimum.csv')

    def get_mpc_results_max_outputs(self, building, output_folder):
        """scenario/outputs/data/optimization"""
        return os.path.join(self.get_mpc_results_folder(output_folder), building + '_outputs_maximum.csv')

    def get_mpc_results_predicted_temperature(self, output_folder):
        """scenario/outputs/data/optimization"""
        return os.path.join(self.get_mpc_results_folder(output_folder), 'predicted_temperature.csv')

    def get_mpc_results_set_temperature(self, output_folder):
        """scenario/outputs/data/optimization"""
        return os.path.join(self.get_mpc_results_folder(output_folder), 'set_temperature.csv')

    def get_mpc_results_min_temperature(self, output_folder):
        """scenario/outputs/data/optimization"""
        return os.path.join(self.get_mpc_results_folder(output_folder), 'minimum_temperature.csv')

    def get_mpc_results_max_temperature(self, output_folder):
        """scenario/outputs/data/optimization"""
        return os.path.join(self.get_mpc_results_folder(output_folder), 'maximum_temperature.csv')

    def get_mpc_results_electric_power(self, output_folder):
        """scenario/outputs/data/optimization"""
        return os.path.join(self.get_mpc_results_folder(output_folder), 'electric_power.csv')

    def get_mpc_results_building_definitions_folder(self, output_folder="mpc-building"):
        return self._ensure_folder(self.get_mpc_results_folder(output_folder), "building-definitions")

    def get_mpc_results_building_definitions_file(self, file_name, output_folder="mpc-building"):
        """scenario/outputs/data/optimization/substations/${building_name}_result.csv"""
        return os.path.join(self.get_mpc_results_building_definitions_folder(output_folder), file_name + ".csv")

    def get_mpc_results_district_plot_streets(self, output_folder="mpc-district"):
        """scenario/outputs/data/optimization/substations/${building_name}_result.csv"""
        return os.path.join(self.get_plots_folder(output_folder), "electric_grid_street.pdf")

    def get_mpc_results_district_plot_grid(self, output_folder="mpc-district"):
        """scenario/outputs/data/optimization/substations/${building_name}_result.csv"""
        return os.path.join(self.get_plots_folder(output_folder), "electric_grid_graph.pdf")


class ReferenceCaseOpenLocator(InputLocator):
    """This is a special InputLocator that extracts the builtin reference case
    (``cea/examples/reference-case-open.zip``) to the temporary folder and uses the baseline scenario in there"""

    already_extracted = False  # only extract once per run

    def __init__(self):

        temp_folder = tempfile.gettempdir()
        project_folder = os.path.join(temp_folder, 'reference-case-open')
        reference_case = os.path.join(project_folder, 'baseline')

        if not ReferenceCaseOpenLocator.already_extracted:
            import cea.examples
            import zipfile
            archive = zipfile.ZipFile(os.path.join(os.path.dirname(cea.examples.__file__), 'reference-case-open.zip'))

            if os.path.exists(project_folder):
                shutil.rmtree(project_folder)
                assert not os.path.exists(project_folder), 'FAILED to remove %s' % project_folder

            archive.extractall(temp_folder)
            ReferenceCaseOpenLocator.already_extracted = True

        super(ReferenceCaseOpenLocator, self).__init__(scenario=reference_case)

    def get_default_weather(self):
        """The reference-case-open uses the Zug weather file..."""
        return self.get_weather('Zug')
