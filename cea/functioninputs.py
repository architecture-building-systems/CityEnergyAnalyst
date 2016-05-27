"""
This is a script containing class definitions for the grouping of input arguments to functions that require a large
number of arguments.
With this classes the inputs to interchangeable functions (e.g. different versions of the calculation of thermal loads)
can be standardized.

author: happle@arch.ethz.ch
date: may 2016
"""

import pandas as pd


class BuildingPropsThermalLoads(object):

    prop_geometry = 0
    prop_architecture = 0
    prop_occupancy = 0
    prop_HVAC_result = 0
    prop_RC_model = 0
    prop_comfort = 0
    prop_internal_loads = 0
    prop_age = 0
    solar = 0

    prop_windows = 0

    # get all properties of building(s)
    def get_props(self, name_building):

        return {'prop_geometry': self.get_prop_geometry(name_building),
                'prop_architecture': self.get_prop_architecture(name_building),
                'prop_occupancy': self.get_prop_occupancy(name_building),
                'prop_HVAC_result': self.get_prop_hvac(name_building),
                'prop_RC_model': self.get_prop_rc_model(name_building),
                'prop_comfort': self.get_prop_comfort(name_building),
                'prop_internal_loads': self.get_prop_internal_loads(name_building),
                'prop_age': self.get_prop_age(name_building),
                'solar': self.get_solar(name_building),
                'prop_windows': self.get_prop_windows(name_building)}

    # get geometry of buildings(s)
    def get_prop_geometry(self, name_building):

        if isinstance(self.prop_geometry, pd.DataFrame):
            return self.prop_geometry.ix[name_building]
        else:
            return False

    # get architecture of buildings(s)
    def get_prop_architecture(self, name_building):
        if isinstance(self.prop_architecture, pd.DataFrame):
            return self.prop_architecture.ix[name_building]
        else:
            return False

    # get occupancy of buildings(s)
    def get_prop_occupancy(self, name_building):
        if isinstance(self.prop_occupancy, pd.DataFrame):
            return self.prop_occupancy.ix[name_building]
        else:
            return False

    # get hvac properties of buildings(s)
    def get_prop_hvac(self, name_building):
        if isinstance(self.prop_HVAC_result, pd.DataFrame):
            return self.prop_HVAC_result.ix[name_building]
        else:
            return False

    # get rc-model properties of buildings(s)
    def get_prop_rc_model(self, name_building):
        if isinstance(self.prop_RC_model, pd.DataFrame):
            return self.prop_RC_model.ix[name_building]
        else:
            return False

    # get comfort properties of buildings(s)
    def get_prop_comfort(self, name_building):
        if isinstance(self.prop_comfort, pd.DataFrame):
            return self.prop_comfort.ix[name_building]
        else:
            return False

    # get internal loads of buildings(s)
    def get_prop_internal_loads(self, name_building):
        if isinstance(self.prop_internal_loads, pd.DataFrame):
            return self.prop_internal_loads.ix[name_building]
        else:
            return False

    # get age properties of buildings(s)
    def get_prop_age(self, name_building):
        if isinstance(self.prop_age, pd.DataFrame):
            return self.prop_age.ix[name_building]
        else:
            return False

    # get solar properties of buildings(s)
    def get_solar(self, name_building):
        if isinstance(self.solar, pd.DataFrame):
            return self.solar.ix[name_building]
        else:
            return False

    # get windows of buildings(s) and their properties
    def get_prop_windows(self, name_building):
        if isinstance(self.prop_windows, pd.DataFrame):
            return self.prop_windows.loc[self.prop_windows['name_building'] == name_building].to_dict('list')
        else:
            return False


