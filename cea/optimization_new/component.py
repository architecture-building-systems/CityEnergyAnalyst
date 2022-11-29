"""
This Component Class defines all properties of individual supply system components in the DCS.

 Properties include:
- the category of components they belong to (primary, secondary, tertiary or storage)
- the component's accepted input and output energy carriers
- the conversion efficiencies (inputs- and outputs related to main energy carriers)
- the sizing of the component
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
# third party libraries
# other files (modules) of this project


class Component(object):
    """
    This is a class that represents supply system componentns of district cooling systems

    :param name: technical name of the component (e.g. "phase-change thermal storage"), defaults to 'xxx'
    :type name: str, optional
    """
    components_database = None

    def __init__(self, name, category):
        self.name = name
        self.category = category
        self.operating_mode = 'efficiencyModel+mainEC'
        self.main_energy_carrier = 'xxx'
        self.input_energy_carriers = 2
        self.output_energy_carriers = 'xxx'
        self.conversion_efficiencies = 'xxx'
        self.capacity = 12

    @staticmethod
    def initialize_class_variables(domain):
        """ Fetch components database from file and save it as a class variable (dict of pd.DataFrames)"""
        Component.components_database = pd.read_excel(domain.locator.get_database_conversion_systems_new(), None)


class AbsorptionChiller(Component):

    name = 'Absorption Chiller'
    category = 'primary'
    linear_efficiency_constant = 0.75

    def __init__(self):
        Component.__init__(self, AbsorptionChiller.name, AbsorptionChiller.category)
        self.efficiency = 'xxx'

    def calculate_efficiency(self, model_type):
        if model_type == 'linear':
            self.efficiency = AbsorptionChiller.linear_efficiency_constant * self.input_energy_carriers / self.capacity
        if model_type == 'complex':
            pass
        else:
            self.efficiency = 1

        return self.efficiency
