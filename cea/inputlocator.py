"""
inputlocator.py - locate input files by name based on the reference folder structure.
"""
import os
import tempfile

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
    def __init__(self, scenario_path):
        self.scenario_path = scenario_path
        self.db_path = os.path.join(os.path.dirname(__file__), 'databases')
        self.weather_path = os.path.join(self.db_path, 'weather')

    @staticmethod
    def _ensure_folder(*components):
        """Return the `*components` joined together as a path to a folder and ensure that that folder exists on disc.
        If it doesn't exist yet, attempt to make it with `os.makedirs`."""
        folder = os.path.join(*components)
        if not os.path.exists(folder):
            os.makedirs(folder)
        return folder

    def get_optimization_results_folder(self):
        """scenario/outputs/data/optimization"""
        return self._ensure_folder(self.scenario_path, 'outputs', 'data', 'optimization')

    def get_optimization_master_results_folder(self):
        """scenario/outputs/data/optimization/master
        Master checkpoints
        """
        return self._ensure_folder(self.get_optimization_results_folder(), "master")

    def get_optimization_slave_results_folder(self):
        """scenario/outputs/data/optimization/slave
        Slave results folder (storage + operation pattern)
        """
        return self._ensure_folder(self.get_optimization_results_folder(), "slave")

    def get_optimization_slave_storage_operation_data(self, configkey):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(),
                            '%(configkey)s_StorageOperationData.csv' % locals())

    def get_optimization_slave_pp_activation_pattern(self, configkey):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(),
                            '%(configkey)s_PPActivationPattern.csv' % locals())

    def get_optimization_slave_slave_cost_data(self, configkey):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(),
                            '%(configkey)s_SlaveCostData.csv' % locals())

    def get_optimization_slave_averaged_cost_data(self, configkey):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(),
                            '%(configkey)s_AveragedCostData.csv' % locals())

    def get_optimization_slave_slave_to_master_cost_emissions_prim_e(self, configkey):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(),
                            '%(configkey)s_SlaveToMasterCostEmissionsPrimE.csv' % locals())

    def get_optimization_slave_primary_energy_by_source(self, configkey):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(),
                            '%(configkey)s_PrimaryEnergyBySource.csv' % locals())

    def get_optimization_slave_slave_detailed_emission_data(self, configkey):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(),
                            '%(configkey)s_SlaveDetailedEmissionData.csv' % locals())

    def get_optimization_slave_slave_detailed_e_prim_data(self, configkey):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(),
                            '%(configkey)s_SlaveDetailedEprimData.csv' % locals())

    def get_optimization_slave_investment_cost_detailed(self, configkey):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(),
                            '%(configkey)s_InvestmentCostDetailed.csv' % locals())

    def get_optimization_slave_storage_flag(self, configkey):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(),
                            '%(configkey)s_StorageFlag.csv' % locals())

    def get_optimization_slave_storage_sizing_parameters(self, configkey):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_slave_results_folder(),
                            '%(configkey)s_Storage_Sizing_Parameters.csv' % locals())

    def get_optimization_disconnected_folder_disc_op_summary(self):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_disconnected_folder(), 'DiscOpSummary.csv')

    def get_optimization_disconnected_folder_building_result(self, buildingname):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_disconnected_folder(), 'DiscOp_' + buildingname + '_result.csv')

    def get_optimization_network_results_summary(self, key):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_network_results_folder(), 'Network_summary_result_' + key + '.csv')

    def get_optimization_network_totals_folder_total(self, indCombi):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_network_totals_folder(), "Total_" + indCombi + ".csv")

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

    def get_optimization_network_layout_pipes_file(self):
        """scenario/outputs/data/optimization/network/layout/DH_PipesData.csv
        Optimized network layout files for pipes of district heating networks
        """
        return os.path.join(self.get_optimization_network_layout_folder(), "PipesData_DH.csv")

    def get_optimization_network_layout_nodes_file(self):
        """scenario/outputs/data/optimization/network/layout/DH_NodesData.csv
        Optimized network layout files for nodes of district heating networks
        """
        return os.path.join(self.get_optimization_network_layout_folder(), "NodesData_DH.csv")

    def get_optimization_network_edge_node_matrix_file(self, network):
        """scenario/outputs/data/optimization/network/layout/DH_EdgeNode.csv or DC_EdgeNode.csv
        Edge-node matrix for a heating or cooling network
        """
        return os.path.join(self.get_optimization_network_layout_folder(), network+"_EdgeNode.csv")

    def get_optimization_network_node_list_file(self, network):
        """scenario/outputs/data/optimization/network/layout/DH_AllNodes.csv or DC_AllNodes.csv
        List of plant and consumer nodes in a district heating or cooling network and their building names
        """
        return os.path.join(self.get_optimization_network_layout_folder(), network+"_AllNodes.csv")

    def get_optimization_network_edge_list_file(self, network):
        """scenario/outputs/data/optimization/network/layout/DH_AllEdges.csv or DC_AllEdges.csv
        List of edges in a district heating or cooling network and their start and end nodes
        """
        return os.path.join(self.get_optimization_network_layout_folder(), network+"_AllEdges.csv")

    def get_optimization_network_layout_massflow_file(self, network):
        """scenario/outputs/data/optimization/network/layout/DH_MassFlow.csv or DC_MassFlow.csv
        Mass flow rates at each edge in a district heating or cooling network
        """
        return os.path.join(self.get_optimization_network_layout_folder(), network+"_MassFlow.csv")

    def get_optimization_network_layout_supply_temperature_file(self, network):
        """scenario/outputs/data/optimization/network/layout/DH_T_Supply.csv or DC_T_Supply.csv
        Supply temperatures at each node for each time step for a district heating or cooling network
        """
        return os.path.join(self.get_optimization_network_layout_folder(), network+"_T_Supply.csv")

    def get_optimization_network_layout_return_temperature_file(self, network):
        """scenario/outputs/data/optimization/network/layout/DH_T_Return.csv or DC_T_Return.csv
        Return temperatures at each node for each time step for a district heating or cooling network
        """
        return os.path.join(self.get_optimization_network_layout_folder(), network+"_T_Return.csv")

    def get_optimization_network_layout_qloss_file(self, network):
        """scenario/outputs/data/optimization/network/layout/DH_T_Return.csv or DC_T_Return.csv
        Return temperatures at each node for each time step for a district heating or cooling network
        """
        return os.path.join(self.get_optimization_network_layout_folder(), network+"_qloss_Supply.csv")

    def get_optimization_network_layout_supply_pressure_file(self, network):
        """scenario/outputs/data/optimization/network/layout/DH_P_Supply.csv or DC_P_Supply.csv
        Supply side pressure for each node in a district heating or cooling network at each time step
        """
        return os.path.join(self.get_optimization_network_layout_folder(), network+"_P_Supply.csv")

    def get_optimization_network_layout_return_pressure_file(self, network):
        """scenario/outputs/data/optimization/network/layout/DH_P_Return.csv or DC_P_Return.csv
        Supply side pressure for each node in a district heating or cooling network at each time step
        """
        return os.path.join(self.get_optimization_network_layout_folder(), network+"_P_Return.csv")

    def get_optimization_network_layout_pressure_drop_file(self, network):
        """scenario/outputs/data/optimization/network/layout/DH_P_DeltaP.csv or DC_P_DeltaP.csv
        Pressure drop over an entire district heating or cooling network at each time step
        """
        return os.path.join(self.get_optimization_network_layout_folder(), network+"_P_DeltaP.csv")

    def get_optimization_network_layout_plant_heat_requirement_file(self, network):
        """scenario/outputs/data/optimization/network/layout/DH_Plant_heat_requirement.csv or DC_Plant_heat_requirement.csv
        Heat requirement at from the plants in a district heating or cooling network
        """
        return os.path.join(self.get_optimization_network_layout_folder(), network+"_Plant_heat_requirement.csv")

    def get_optimization_network_totals_folder(self):
        """scenario/outputs/data/optimization/network/totals
        Total files (inputs to substation + network in master)
        """
        return self._ensure_folder(self.get_optimization_network_results_folder(), "totals")

    def get_optimization_disconnected_folder(self):
        """scenario/outputs/data/optimization/disconnected
        Operation pattern for disconnected buildings"""
        return self._ensure_folder(self.get_optimization_results_folder(), "disconnected")

    def get_optimization_checkpoint(self, generation):
        """scenario/outputs/data/calibration/clustering/checkpoints/..."""
        return os.path.join(self.get_optimization_master_results_folder(),
                            'CheckPoint_'+str(generation))

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
                            'CheckPoint_uncertainty_'+str(generation))

    def get_measurements(self):
        """scenario/inputs/
        Operation pattern for disconnected buildings"""
        return self._ensure_folder(self.scenario_path, 'inputs', 'building-metering',)

    def get_optimization_disconnected_result_file(self, building_name):
        """scenario/outputs/data/optimization/disconnected/DiscOp_${building_name}_result.csv"""
        return os.path.join(self.get_optimization_disconnected_folder(),
                            "DiscOp_%(building_name)s_result.csv" % locals())

    def get_optimization_substations_folder(self):
        """scenario/outputs/data/optimization/substations
        Substation results for disconnected buildings"""
        return self._ensure_folder(self.get_optimization_results_folder(), "substations")

    def get_optimization_substations_results_file(self, building_name):
        """scenario/outputs/data/optimization/substations/${building_name}_result.csv"""
        return os.path.join(self.get_optimization_substations_folder(),  "%(building_name)s_result.csv" % locals())

    def get_optimization_substations_total_file(self, genome):
        """scenario/outputs/data/optimization/substations/Total_${genome}.csv"""
        return os.path.join(self.get_optimization_substations_folder(),  "Total_%(genome)s.csv" % locals())

    def get_optimization_clustering_folder(self):
        """scenario/outputs/data/optimization/clustering_main
        Clustering results for disconnected buildings"""
        return self._ensure_folder(self.get_optimization_results_folder(), "clustering_main")

    def get_potentials_results_folder(self):
        """scenario/outputs/data/potentials"""
        return self._ensure_folder(self.scenario_path, 'outputs', 'data', 'potentials')

    def get_potentials_solar_folder(self):
        """scenario/outputs/data/potentials/solar
        Contains raw solar files
        """
        return self._ensure_folder(self.get_potentials_results_folder(), "solar")

    # optimization
    def get_sewage_heat_potential(self):
        return os.path.join(self.get_potentials_results_folder(), "SWP.csv")

    # resource potential assessment
    def get_geothermal_potential(self):
        """scenario/outputs/data/potentials/geothermal.csv"""
        return os.path.join(self.get_potentials_results_folder(), "geothermal.csv")

    # DATABASES
    def get_default_weather(self):
        """weather/Zug-2010.epw
        path to database of archetypes file Archetypes_properties.xlsx"""
        return os.path.join(self.weather_path, 'Zug.epw')

    def get_weather(self, name):
        """weather/{name}.epw"""
        weather_file = os.path.join(self.weather_path, name + '.epw')
        if not os.path.exists(weather_file):
            return self.get_default_weather()
        return weather_file

    def get_weather_names(self):
        """Return a list of all installed epw files in the system"""
        weather_names = [os.path.splitext(f)[0] for f in os.listdir(self.weather_path)]
        return weather_names

    def get_archetypes_properties(self):
        """db/Archetypes/Archetypes_properties.xlsx
        path to database of archetypes file Archetypes_properties.xlsx"""
        return os.path.join(self.db_path, 'archetypes', 'construction_properties_CH.xlsx')

    def get_archetypes_schedules(self):
        """db/Archetypes/Archetypes_schedules.xlsx
        path to database of archetypes file Archetypes_HVAC_properties.xlsx"""
        return os.path.join(self.db_path, 'archetypes', 'occupancy_schedules_SIA.xlsx')

    def get_life_cycle_inventory_supply_systems(self):
        """databases/lifecycle/LCA_infrastructure.csv"""
        return os.path.join(self.db_path, 'lifecycle', 'LCA_infrastructure.xlsx')

    def get_life_cycle_inventory_building_systems(self):
        """databases/lifecycle/LCA_infrastructure.csv"""
        return os.path.join(self.db_path, 'lifecycle', 'LCA_buildings.xlsx')

    def get_technical_emission_systems(self):
        """databases/CH/Systems/emission_systems.csv"""
        return os.path.join(self.db_path, 'systems',  'emission_systems.xls')

    def get_envelope_systems(self):
        """databases/CH/Systems/emission_systems.csv"""
        return os.path.join(self.db_path, 'systems',  'envelope_systems.xls')

    def get_thermal_networks(self):
        """db/Systems/thermal_networks.xls"""
        return os.path.join(self.db_path, 'systems',  'thermal_networks.xls')

    def get_data_benchmark(self):
        """databases/CH/Benchmarks/benchmark_targets.xls"""
        return os.path.join(self.db_path, 'benchmarks', 'benchmark_2000W.xls')

    def get_data_mobility(self):
        """databases/CH/Benchmarks/mobility.xls"""
        return os.path.join(self.db_path, 'benchmarks', 'mobility.xls')

    def get_uncertainty_db(self):
        """databases/CH/Uncertainty/uncertainty_distributions.xls"""
        return os.path.join(self.db_path, 'uncertainty', 'uncertainty_distributions.xls')

    def get_uncertainty_parameters(self):
        """databases/CH/Uncertainty/uncertainty_distributions.xls"""
        return os.path.join(self.db_path, 'uncertainty')

    def get_uncertainty_results_folder(self):
        return self._ensure_folder(self.scenario_path, 'outputs', 'data', 'uncertainty')

    def get_supply_systems_database(self):
        """databases/CH/Systems/etechnologies.xls"""
        return os.path.join(self.db_path, 'systems',  'supply_systems.xls')

    # INPUTS

    def get_building_geometry_folder(self):
        """scenario/inputs/building-geometry/"""
        return os.path.join(self.scenario_path, 'inputs', 'building-geometry')

    def get_building_geometry(self):
        """scenario/inputs/building-geometry/zone.shp"""
        return os.path.join(self.scenario_path, 'inputs', 'building-geometry', 'zone.shp')

    def get_building_geometry_citygml(self):
        """scenario/outputs/data/solar-radiation/district.gml"""
        return os.path.join(self.get_solar_radiation_folder(), 'district.gml')

    def get_district(self):
        """scenario/inputs/building-geometry/district.shp"""
        return os.path.join(self.scenario_path, 'inputs', 'building-geometry', 'district.shp')

    def get_building_age(self):
        """scenario/inputs/building-properties/age.dbf"""
        return os.path.join(self.scenario_path, 'inputs', 'building-properties', 'age.dbf')

    def get_building_occupancy(self):
        """scenario/inputs/building-properties/building_occupancy.dbf"""
        return os.path.join(self.scenario_path, 'inputs', 'building-properties', 'occupancy.dbf')

    def get_building_supply(self):
        """scenario/inputs/building-properties/building_supply.dbf"""
        return os.path.join(self.scenario_path, 'inputs', 'building-properties', 'supply_systems.dbf')

    def get_building_internal(self):
        """scenario/inputs/building-properties/internal_loads.dbf"""
        return os.path.join(self.scenario_path, 'inputs', 'building-properties', 'internal_loads.dbf')

    def get_building_comfort(self):
        """scenario/inputs/building-properties/indoor_comfort.dbf"""
        return os.path.join(self.scenario_path, 'inputs', 'building-properties', 'indoor_comfort.dbf')

    def get_building_hvac(self):
        """scenario/inputs/building-properties/technical_systems.dbf"""
        return os.path.join(self.scenario_path, 'inputs', 'building-properties', 'technical_systems.dbf')

    def get_building_architecture(self):
        """scenario/inputs/building-properties/architecture.dbf
        This file is generated by the properties script.
        This file is used in the embodied energy script (cea/embodied.py)
        and the demand script (cea/demand_main.py)"""
        return os.path.join(self.scenario_path, 'inputs', 'building-properties', 'architecture.dbf')

    def get_building_overrides(self):
        """scenario/inputs/building-properties/overrides.csv
        This file contains overrides to the building properties input files. They are applied after reading
        those files and are matched by column name.
        """
        return os.path.join(self.scenario_path, 'inputs', 'building-properties', 'overrides.csv')

    def get_terrain(self):
        """scenario/inputs/topography/terrain.tif"""
        return os.path.join(self.scenario_path, 'inputs', 'topography', 'terrain.tif')

    def get_network_layout_edges_shapefile(self, network):
        """scenario/inputs/network/DH or DC/network-edges.shp"""
        return os.path.join(self.scenario_path, 'inputs', 'network', network, 'network-edges.shp')

    def get_network_layout_nodes_shapefile(self, network):
        """scenario/inputs/network/DH or DC/network-nodes.shp"""
        return os.path.join(self.scenario_path, 'inputs', 'network', network, 'network-nodes.shp')

    def get_network_layout_pipes_csv_file(self, network):
        """scenario/outputs/data/optimization/network/layout/DH_PipesData.csv or DC_PipesData.csv
        Network layout files for pipes of district heating or cooling networks
        """
        return os.path.join(self.get_optimization_network_layout_folder(), "PipesData_"+network+".csv")

    def get_network_layout_nodes_csv_file(self, network):
        """scenario/outputs/data/optimization/network/layout/DH_NodesData.csv or DC_NodesData.csv
        Network layout files for nodes of district heating or cooling networks
        """
        return os.path.join(self.get_optimization_network_layout_folder(), "NodesData_"+network+".csv")

    def get_edge_mass_flow_csv_file(self, network_type):
        """scenario/outputs/data/optimization/network/layout/DH_NodesData.csv or DC_NodesData.csv
        Network layout files for nodes of district heating or cooling networks
        """
        return os.path.join(self.get_optimization_network_layout_folder(), 'NominalEdgeMassFlow_' +
                             network_type + '.csv')

    def get_daysim_mat(self):
        """this gets the file that documents all of the radiance/default_materials"""
        return os.path.join(os.path.dirname(__file__), 'resources', 'radiation_daysim', 'default_materials.rad')

    # OUTPUTS

    ##SOLAR-RADIATION
    def get_radiation(self):  #todo: delete if not used
        """scenario/outputs/data/solar-radiation/radiation.csv"""
        return os.path.join(self._ensure_folder(self.get_solar_radiation_folder()), 'radiation.csv')

    def get_solar_radiation_folder(self):
        """scenario/outputs/data/solar-radiation"""
        return self._ensure_folder(self.scenario_path, 'outputs', 'data', 'solar-radiation')

    def get_radiation_building(self, building_name):
        """scenario/outputs/data/solar-radiation/radiation.csv"""
        solar_radiation_folder = os.path.join(self.scenario_path, 'outputs', 'data', 'solar-radiation')
        if not os.path.exists(solar_radiation_folder):
            os.makedirs(solar_radiation_folder)
        return os.path.join(solar_radiation_folder, '%s_insolation_Whm2.csv' %building_name)

    def get_radiation_metadata(self, building_name):
        """scenario/outputs/data/solar-radiation/radiation.csv"""
        solar_radiation_folder = os.path.join(self.scenario_path, 'outputs', 'data', 'solar-radiation')
        if not os.path.exists(solar_radiation_folder):
            os.makedirs(solar_radiation_folder)
        return os.path.join(solar_radiation_folder, '%s_geometry.csv' %building_name)

    def get_building_list(self):
        """scenario/outputs/data/solar-radiation/radiation.csv"""
        solar_radiation_folder = os.path.join(self.scenario_path, 'outputs', 'data', 'solar-radiation')
        return os.path.join(solar_radiation_folder, 'radiation.csv')

    def get_3D_geometry_folder(self):
        """scenario/inputs/3D-geometries"""
        return self._ensure_folder(os.path.join(self.scenario_path, 'inputs', '3D-geometries'))

    def get_solar_radiation_folder(self):
        """scenario/outputs/data/solar-radiation"""
        return os.path.join(self.scenario_path, 'outputs', 'data', 'solar-radiation')

    def get_surface_properties(self):
        """scenario/outputs/data/solar-radiation/properties_surfaces.csv"""
        return os.path.join(self.get_solar_radiation_folder(), 'properties_surfaces.csv')

    def get_sensitivity_output(self, method, samples):
        """scenario/outputs/data/sensitivity-analysis/sensitivity_${METHOD}_${SAMPLES}.xls"""
        return os.path.join(self.scenario_path, 'outputs', 'data', 'sensitivity-analysis',
                            'sensitivity_%(method)s_%(samples)s.xls' % locals())

    def get_sensitivity_plots_file(self, parameter):
        """scenario/outputs/plots/sensitivity/${PARAMETER}.pdf"""
        return os.path.join(self.scenario_path, 'outputs', 'plots', 'sensitivity', '%s.pdf' % parameter)

    ## POTENTIALS #FIXME: find better placement for these two locators

    def solar_potential_folder(self):
        return self._ensure_folder(self.scenario_path, 'outputs', 'data', 'potentials','solar')

    def PV_results(self, building_name):
        """scenario/outputs/data/potentials/solar/{building_name}_PV.csv"""
        return os.path.join(self.solar_potential_folder(), '%s_PV.csv' % building_name)

    def metadata_results(self, building_name):
        """scenario/outputs/data/potentials/solar/{building_name}_PV.csv"""
        solar_potential_folder = os.path.join(self.scenario_path, 'outputs', 'data', 'potentials','solar')
        return os.path.join(solar_potential_folder, '%s_sensors.csv' % building_name)

    # DEMAND

    def get_demand_results_folder(self):
        """scenario/outputs/data/demand"""
        return self._ensure_folder(self.scenario_path, 'outputs', 'data', 'demand')

    def get_total_demand(self):
        """scenario/outputs/data/demand/Total_demand.csv"""
        return os.path.join(self.get_demand_results_folder(), 'Total_demand.csv')

    def get_demand_results_file(self, building_name):
        """scenario/outputs/data/demand/{building_name}.csv"""
        return os.path.join(self.get_demand_results_folder(), '%(building_name)s.csv' % locals())

    # CALIBRATION
    def get_calibration_folder(self):
        """scenario/outputs/data/calibration"""
        return self._ensure_folder(self.scenario_path, 'outputs', 'data', 'calibration')

    def get_calibration_clustering_folder(self):
        """scenario/outputs/data/calibration"""
        return self._ensure_folder(self.get_calibration_folder(), 'clustering')

    def get_calibration_clustering_clusters_folder(self):
        """scenario/outputs/data/calibration"""
        return self._ensure_folder(self.get_calibration_clustering_folder(), 'clusters')

    def get_demand_measured_folder(self):
        """scenario/outputs/data/demand"""
        return self._ensure_folder(self.scenario_path, 'inputs', 'building-metering')

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
                            'cp_gen_'+str(generation)+'_building_'+building)

    def get_calibration_cluster_mcda_folder(self):
        return self._ensure_folder(self.get_calibration_clustering_folder(), "multicriteria")

    def get_calibration_cluster_mcda(self, generation):
        return os.path.join(self.get_calibration_cluster_mcda_folder(), "mcda_gen_"+str(generation)+".csv")

    def get_calibration_clusters_names(self):
        """scenario/outputs/data/demand/{sax_name}.csv"""
        return os.path.join(self.get_calibration_clustering_clusters_folder(), 'sax_names.csv')

    def get_calibration_clustering_plots_folder(self):
        return self._ensure_folder(self.get_calibration_clustering_folder(), "plots")
    ##EMISSIONS
    def get_lca_emissions_results_folder(self):
        """scenario/outputs/data/emissions"""
        lca_emissions_results_folder = os.path.join(self.scenario_path, 'outputs', 'data', 'emissions')
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

    ##GRAPHS
    def get_demand_plots_folder(self):
        """scenario/outputs/plots/timeseries"""
        return self._ensure_folder(self.scenario_path, 'outputs', 'plots', 'timeseries')

    def get_demand_plots_file(self, building_name):
        """scenario/outputs/plots/timeseries/{building_name}.pdf"""
        return os.path.join(self.get_demand_plots_folder(), '%(building_name)s.pdf' % locals())

    def get_timeseries_plots_file(self, building_name):
        """scenario/outputs/plots/timeseries/{building_name}.html"""
        return os.path.join(self.get_demand_plots_folder(), '%(building_name)s.html' % locals())

    def get_benchmark_plots_file(self):
        """scenario/outputs/plots/graphs/Benchmark_scenarios.pdf"""
        return os.path.join(self._ensure_folder(self.scenario_path, 'outputs', 'plots', 'graphs'),
                            'Benchmark_scenarios.pdf')

    def get_optimization_plots_folder(self):
        """scenario/outputs/plots/graphs/Benchmark_scenarios.pdf"""
        return os.path.join(self._ensure_folder(self.scenario_path, 'outputs', 'plots', 'graphs'))


    # HEATMAPS
    def get_heatmaps_demand_folder(self):
        """scenario/outputs/plots/heatmaps"""
        return self._ensure_folder(self.scenario_path, 'outputs', 'plots', 'heatmaps')

    def get_heatmaps_emission_folder(self):
        """scenario/outputs/plots/heatmaps"""
        return self._ensure_folder(self.scenario_path, 'outputs', 'plots', 'heatmaps')

    # OTHER
    def get_temporary_folder(self):
        """Temporary folder as returned by `tempfile`."""
        return tempfile.gettempdir()

    def get_temporary_file(self, filename):
        """Returns the path to a file in the temporary folder with the name `filename`"""
        return os.path.join(self.get_temporary_folder(), filename)