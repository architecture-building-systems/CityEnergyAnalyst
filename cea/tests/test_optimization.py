import cea.config
import cea.inputlocator
import cea.globalvar
from cea.optimization.optimization_main import main as optimization_main
from cea.datamanagement.data_helper import data_helper
from cea. demand.demand_main import demand_calculation
from cea.resources.radiation_daysim.radiation_main import main as radiation_main
from cea.technologies.solar.photovoltaic import main as photovoltaic_main
from cea.technologies.solar.photovoltaic_thermal import main as photovoltaic_thermal_main
from cea.technologies.solar.solar_collector import main as solar_collector_main
from cea.resources.sewage_heat_exchanger import main as sewage_potential_main
from cea.resources.lake_potential import main as lake_potential_main
from cea.technologies.thermal_network.thermal_network_matrix import main as thermal_network_main
from cea.technologies.thermal_network.network_layout.main import main as thermal_network_layout
from cea.supply.supply_system_simulation import main as supply_system_simulation

# get global variables
gv = cea.globalvar.GlobalVariables()

# TEST HEATING SYSTEM OPTIMIZATION
# define input locator for reference-case-open and get corresponding weather file
locator_CH = cea.inputlocator.ReferenceCaseOpenLocator()
# create config file for Swiss case study
config_CH = cea.config.Configuration()
config_CH.scenario = locator_CH.scenario
config_CH.weather = locator_CH.weather_path
config_CH.region = 'CH'
# run data helper
data_helper(locator_CH, config_CH, prop_architecture_flag=True, prop_hvac_flag=True, prop_comfort_flag=True,
            prop_internal_loads_flag=True, prop_supply_systems_flag=True, prop_restrictions_flag=True)
# run demand simulation
demand_calculation(locator_CH, config_CH)
# run photovoltaic potential calculation
photovoltaic_main(config_CH)
# run solar collector potential calculation
for technology in ['ET', 'FP']:
    config_CH.solar.type_scpanel = technology
    solar_collector_main(config_CH)
# run photovoltaic thermal potential calculation
photovoltaic_thermal_main(config_CH)
# run sewage heat recovery potential calculation
sewage_potential_main(config_CH)
# run lake potential calculation
lake_potential_main(config_CH)
# run thermal network calculation
config_CH.thermal_network.network_type = 'DH'
thermal_network_main(config_CH)
# set optimization parameters in config file and run optimization
config_CH.optimization.initialind = 2
config_CH.optimization.ngen = 2
config_CH.district_heating_network = True
config_CH.district_cooling_network = False
optimization_main(config_CH)

# TEST COOLING SYSTEM OPTIMIZATION
# define input locator for reference-case-WTP and get corresponding weather file
locator_SG = cea.inputlocator.ReferenceCaseWTPLocator()
# create config file for Singapore case study
config_SG = cea.config.Configuration()
config_SG.scenario = locator_SG.scenario
config_SG.weather = locator_SG.weather_path
config_SG.region = 'SG'
# run data helper
data_helper(locator_SG, config_SG, prop_architecture_flag=True, prop_hvac_flag=True, prop_comfort_flag=True,
            prop_internal_loads_flag=True, prop_supply_systems_flag=True, prop_restrictions_flag=True)
# run solar radiation calculation
radiation_main(config_SG)
# run demand simulation
demand_calculation(locator_SG, config_SG)
# run photovoltaic potential calculationf
photovoltaic_main(config_SG)
# run solar collector potential calculation
for technology in ['ET', 'FP']:
    config_SG.solar.type_scpanel = technology
    solar_collector_main(config_SG)
# run photovoltaic thermal potential calculation
photovoltaic_thermal_main(config_SG)
# run sewage heat recovery potential calculation
sewage_potential_main(config_SG)
# run lake potential calculation
lake_potential_main(config_SG)
# create thermal network layout
thermal_network_layout(config_SG)
# set thermal network type and run thermal network calculation
config_SG.thermal_network.network_type = 'DC'
thermal_network_main(config_SG)
# set decentralized system simulation parameters and run decentralized system simulation
config_SG.supply_system_simulation.centralized_vcc = 0.0
config_SG.supply_system_simulation.centralized_ach = 0.0
config_SG.supply_system_simulation.centralized_storage = 0.0
config_SG.supply_system_simulation.dc_connected_buildings = ''
supply_system_simulation(config_SG)
# set optimization parameters in config file and run optimization
config_SG.optimization.initialind = 2
config_SG.optimization.ngen = 2
config_SG.district_heating_network = False
config_SG.district_cooling_network = True
optimization_main(config_SG)
