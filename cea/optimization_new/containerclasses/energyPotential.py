"""
Energy Potential Class:
defines the energy potential corresponding to a certain energy carrier in the optimisation domain:
- The building's unique identifier (i.e. 'Name' from the input editor)
- The building's location
- The demand profile of the building
"""

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2022, Cooling Singapore"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "NA"
__email__ = "mathias.niffeler@sec.ethz.ch"
__status__ = "Production"

import pandas as pd
import numpy as np
from os.path import exists

from cea.optimization_new.containerclasses.energyFlow import EnergyFlow
from cea.optimization_new.containerclasses.energyCarrier import EnergyCarrier


class EnergyPotential(object):
    time_frame = 8760  # placeholder, this will be made variable in the future

    def __init__(self):
        self._type = 'e.g. SolarPV'
        self._scale = 'Building, Network or Domain'
        self.main_potential = EnergyFlow()
        self.auxiliary_potential = EnergyFlow()
        self.main_building_profiles = pd.DataFrame()
        self.auxiliary_building_profiles = pd.DataFrame()

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, new_type):
        if new_type in ['SolarPV', 'SolarPVT', 'SolarCollectorET', 'SolarCollectorFP', 'WaterBody', 'Geothermal', 'Sewage']:
            self._type = new_type
        else:
            raise ValueError("Unexpected type of energy potential. "
                             "Please assign one of the valid energy potential types: "
                             "SolarPV, SolarPVT, SolarCollectorET, SolarCollectorFP, WaterBody, Geothermal, Sewage")

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, new_scale):
        if new_scale in ['Building', 'Network', 'Domain']:
            self._scale = new_scale
        else:
            raise ValueError("Unexpected scale for the energy potential. "
                             "Please assign one a valid scale: "
                             "Building, Network, Domain")

    def load_PV_potential(self, locator, building_codes):
        self.type = 'SolarPV'
        self.scale = 'Building'
        pv_potential_files = np.vectorize(locator.PV_results)(building_codes)
        potentials = self._get_building_potentials(pv_potential_files, building_codes, 'E_PV_gen_kWh')
        if potentials:
            main_energy_carrier = 'E230AC'
            self.main_potential.generate('source', 'secondary', main_energy_carrier, potentials['main_profile'])
            self.main_building_profiles = potentials['main_building_profiles']
            return self
        else:
            return None

    def load_PVT_potential(self, locator, building_codes):
        self.type = 'SolarPVT'
        self.scale = 'Building'
        pvt_potential_files = np.vectorize(locator.PVT_results)(building_codes)
        potentials = self._get_building_potentials(pvt_potential_files, building_codes,
                                                   'E_PVT_gen_kWh', 'T_PVT_re_C', 'Q_PVT_gen_kWh')
        if potentials:
            main_energy_carrier = 'E230AC'
            auxiliary_energy_carrier = EnergyCarrier.temp_to_thermal_ec('water', potentials['average_temp'])
            self.main_potential.generate('source', 'secondary', main_energy_carrier, potentials['main_profile'])
            self.main_building_profiles = potentials['main_building_profiles']
            self.auxiliary_potential.generate('source', 'secondary', auxiliary_energy_carrier, potentials['auxiliary_profile'])
            self.auxiliary_building_profiles = potentials['auxiliary_building_profiles']
            return self
        else:
            return None

    def load_SCET_potential(self, locator, building_codes):
        self.type = 'SolarCollectorET'
        self.scale = 'Building'
        scet_potential_files = np.vectorize(locator.SC_results)(building_codes, "ET")
        potentials = self._get_building_potentials(scet_potential_files, building_codes,
                                                                   'Q_SC_gen_kWh', 'T_SC_re_C')
        if potentials:
            main_energy_carrier = EnergyCarrier.temp_to_thermal_ec('water', potentials['average_temp'])
            self.main_potential.generate('source', 'secondary', main_energy_carrier, potentials['main_profile'])
            self.main_building_profiles = potentials['main_building_profiles']
            return self
        else:
            return None

    def load_SCFP_potential(self, locator, building_codes):
        self.type = 'SolarCollectorFP'
        self.scale = 'Building'
        scfp_potential_files = np.vectorize(locator.SC_results)(building_codes, "FP")
        potentials = self._get_building_potentials(scfp_potential_files, building_codes,
                                                                   'Q_SC_gen_kWh', 'T_SC_re_C')
        if potentials:
            main_energy_carrier = EnergyCarrier.temp_to_thermal_ec('water', potentials['average_temp'])
            self.main_potential.generate('source', 'secondary', main_energy_carrier, potentials['main_profile'])
            self.main_building_profiles = potentials['main_building_profiles']
            return self
        else:
            return None

    def load_geothermal_potential(self, geothermal_potential_file):
        self.type = 'Geothermal'
        self.scale = 'Domain'
        if exists(geothermal_potential_file):
            geothermal_potential = pd.read_csv(geothermal_potential_file)
            main_potential_flow_profile = geothermal_potential.QGHP_kW
            average_return_temperature = self._get_average_temp(geothermal_potential.Ts_C)
            main_energy_carrier = EnergyCarrier.temp_to_thermal_ec('water', average_return_temperature)
            self.main_potential.generate('source', 'secondary', main_energy_carrier, main_potential_flow_profile)
            return self
        else:
            return None

    def load_water_body_potential(self, water_body_potential_file):
        self.type = 'WaterBody'
        self.scale = 'Domain'
        if exists(water_body_potential_file):
            water_body_potential = pd.read_csv(water_body_potential_file)
            main_potential_flow_profile = water_body_potential.QLake_kW
            average_return_temperature = self._get_average_temp(water_body_potential.Ts_C)
            main_energy_carrier = EnergyCarrier.temp_to_thermal_ec('water', average_return_temperature)
            self.main_potential.generate('source', 'secondary', main_energy_carrier, main_potential_flow_profile)
            return self
        else:
            return None

    def load_sewage_potential(self, sewage_potential_file):
        self.type = 'Sewage'
        self.scale = 'Domain'
        if exists(sewage_potential_file):
            sewage_potential = pd.read_csv(sewage_potential_file)
            main_potential_flow_profile = sewage_potential.Qsw_kW
            average_return_temperature = self._get_average_temp(sewage_potential.Ts_C)
            main_energy_carrier = EnergyCarrier.temp_to_thermal_ec('water', average_return_temperature)
            self.main_potential.generate('source', 'secondary', main_energy_carrier, main_potential_flow_profile)
            return self
        else:
            return None

    def _get_building_potentials(self, energy_potential_files, building_codes, main_potential_column_name,
                                 temperature_column_name=None, auxiliary_potential_column_name=None):
        """
        Gets main and auxiliary potentials from the stored energy potential files and stores them in the corresponding
        object attributes. In case a temperature column name is indicated, the average temperature (when operating
        the corresponding component at maximum potential) is returned.
        """
        # check if there are potential files for any of the buildings
        if not any([exists(file) for file in energy_potential_files]):
            print(f"No {self.type} potentials could be found for the indicated buildings. If you would like to include "
                  f"potentials, consider running potentials scripts and then rerun the optimisation.")
            return None
        # initialise necessary variables
        nbr_of_files = len(energy_potential_files)
        average_temps = [np.nan] * nbr_of_files
        main_potential = pd.DataFrame(0.0, index=np.arange(self.time_frame),
                                      columns=pd.concat([pd.Series(['domain_potential']), building_codes]))
        if auxiliary_potential_column_name is not None:
            auxiliary_potential = pd.DataFrame(0.0, index=np.arange(self.time_frame),
                                               columns=pd.concat([pd.Series(['domain_potential']), building_codes]))
        else:
            auxiliary_potential = pd.DataFrame(columns=pd.concat([pd.Series(['domain_potential']), building_codes]))
        # if specific potential file for a building exists, save potential to object attribute (pd.Dataframe)
        for (file, i) in zip(energy_potential_files, np.arange(nbr_of_files)):
            if exists(file):
                pvt_potential = pd.read_csv(file)
                main_potential[building_codes[i]] = pvt_potential[main_potential_column_name]
                if temperature_column_name is not None:
                    average_temps[i] = self._get_average_temp(pvt_potential[temperature_column_name], building_codes[i])
                if auxiliary_potential_column_name is not None:
                    auxiliary_potential[building_codes[i]] = pvt_potential[auxiliary_potential_column_name]
        # calculate total potential across the domain
        main_potential['domain_potential'] = main_potential[building_codes].sum(axis=1)
        if auxiliary_potential_column_name is not None:
            auxiliary_potential['domain_potential'] = auxiliary_potential[building_codes].sum(axis=1)
        # if thermal(!) energy potential: return average return temperature
        if temperature_column_name is not None:
            average_temperature = np.nanmean(average_temps)
        else:
            average_temperature = None
        # return potentials and average temperature
        return {'main_profile': main_potential['domain_potential'],
                'main_building_profiles': main_potential[building_codes],
                'auxiliary_profile': auxiliary_potential['domain_potential'],
                'auxiliary_building_profiles': auxiliary_potential[building_codes],
                'average_temp': average_temperature}

    def _get_average_temp(self, temperature_series, building_code=None):
        average_temp = np.mean(temperature_series)
        if all(np.isnan(temperature_series)):
            if building_code is None:
                print(f"There seems to be a problem with the {self.type} potential! "
                      f"Please check the corresponding .csv-file.")
            else:
                print(f"There seems to be a problem with the {self.type} potential of building {building_code}! "
                      f"Please check the corresponding .csv-file.")
        elif average_temp == 0:
            average_temp = np.nan
        return average_temp
