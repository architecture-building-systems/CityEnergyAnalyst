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

# imports
# standard libraries
import pandas as pd
import numpy as np
from os.path import exists
# third party libraries
# other files (modules) of this project


class EnergyPotential(object):
    time_frame = 8760

    def __init__(self):
        self._type = 'e.g. SolarPV'
        self._scale = 'Building, Network or Domain'
        self.main_potential = pd.DataFrame(0, index=np.arange(self.time_frame), columns=['domain_potential'])
        self.main_energy_carrier = None
        self.auxiliary_potential = pd.DataFrame(0, index=np.arange(self.time_frame), columns=['domain_potential'])
        self.auxiliary_energy_carrier = None

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
        self.main_potential = pd.DataFrame(0.0, index=np.arange(self.time_frame),
                                           columns=pd.concat([pd.Series(['domain_potential']), building_codes]))
        pv_potential_files = np.vectorize(locator.PV_results)(building_codes)
        i = 0
        for file in pv_potential_files:
            if exists(file):
                self.main_potential[building_codes[i]] = pd.read_csv(file).E_PV_gen_kWh
            else:
                self.main_potential[building_codes[i]] = pd.Series(0.0)
            i += 1
        self.main_potential['domain_potential'] = self.main_potential[building_codes].sum(axis=1)
        self.main_energy_carrier = 'Electricity'
        return self

    def load_PVT_potential(self, locator, building_codes):
        self.type = 'SolarPVT'
        self.scale = 'Building'
        self.main_potential = pd.DataFrame(0.0, index=np.arange(self.time_frame),
                                           columns=pd.concat([pd.Series(['domain_potential']), building_codes]))
        self.auxiliary_potential = pd.DataFrame(0.0, index=np.arange(self.time_frame),
                                                columns=pd.concat([pd.Series(['domain_potential']), building_codes]))
        pvt_potential_files = np.vectorize(locator.PVT_results)(building_codes)
        i = 0
        for file in pvt_potential_files:
            if exists(file):
                pvt_potential = pd.read_csv(file)
                self.main_potential[building_codes[i]] = pvt_potential.E_PVT_gen_kWh
                self.auxiliary_potential[building_codes[i]] = pvt_potential.Q_PVT_gen_kWh
            else:
                self.main_potential[building_codes[i]] = pd.Series(0.0)
                self.auxiliary_potential[building_codes[i]] = pd.Series(0.0)
            i += 1
        self.main_potential['domain_potential'] = self.main_potential[building_codes].sum(axis=1)
        self.auxiliary_potential['domain_potential'] = self.auxiliary_potential[building_codes].sum(axis=1)
        self.main_energy_carrier = 'Electricity'
        self.auxiliary_energy_carrier = 'Thermal'
        return self

    def load_SCET_potential(self, locator, building_codes):
        self.type = 'SolarCollectorET'
        self.scale = 'Building'
        self.main_potential = pd.DataFrame(0.0, index=np.arange(self.time_frame),
                                           columns=pd.concat([pd.Series(['domain_potential']), building_codes]))
        scet_potential_files = np.vectorize(locator.SC_results)(building_codes, "ET")
        i = 0
        for file in scet_potential_files:
            if exists(file):
                self.main_potential[building_codes[i]] = pd.read_csv(file).Q_SC_gen_kWh
            else:
                self.main_potential[building_codes[i]] = pd.Series(0.0)
            i += 1
        self.main_potential['domain_potential'] = self.main_potential[building_codes].sum(axis=1)
        self.main_energy_carrier = 'Thermal'
        return self

    def load_SCFP_potential(self, locator, building_codes):
        self.type = 'SolarCollectorFP'
        self.scale = 'Building'
        self.main_potential = pd.DataFrame(0.0, index=np.arange(self.time_frame),
                                           columns=pd.concat([pd.Series(['domain_potential']), building_codes]))
        scfp_potential_files = np.vectorize(locator.SC_results)(building_codes, "ET")
        i = 0
        for file in scfp_potential_files:
            if exists(file):
                self.main_potential[building_codes[i]] = pd.read_csv(file).Q_SC_gen_kWh
            else:
                self.main_potential[building_codes[i]] = pd.Series(0.0)
            i += 1
        self.main_potential['domain_potential'] = self.main_potential[building_codes].sum(axis=1)
        self.main_energy_carrier = 'Thermal'
        return self

    def load_geothermal_potential(self, geothermal_potential_file):
        self.type = 'Geothermal'
        self.scale = 'Domain'
        if exists(geothermal_potential_file):
            self.main_potential = pd.read_csv(geothermal_potential_file).QGHP_kW
        self.main_energy_carrier = 'Thermal'
        return self

    def load_water_body_potential(self, water_body_potential_file):
        self.type = 'WaterBody'
        self.scale = 'Domain'
        if exists(water_body_potential_file):
            self.main_potential = pd.read_csv(water_body_potential_file).QLake_kW
        self.main_energy_carrier = 'Thermal'
        return self

    def load_sewage_potential(self, sewage_potential_file):
        self.type = 'Sewage'
        self.scale = 'Domain'
        if exists(sewage_potential_file):
            self.main_potential = pd.read_csv(sewage_potential_file).Qsw_kW
        self.main_energy_carrier = 'Thermal'
        return self
