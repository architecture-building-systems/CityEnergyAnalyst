# -*- coding: utf-8 -*-


from __future__ import division
from cea.demand import rc_model_SIA
from cea.utilities import helpers

__author__ = "Gabriel Happle"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def has_heating_system(bpr):
    """
    determines whether a building has a heating system installed or not

    bpr : building properties row object

    :returns:
    :rtype: bool
    """

    if bpr.hvac['type_hs'] in {'T1', 'T2', 'T3', 'T4'}:
        return True
    elif bpr.hvac['type_hs'] in {'T0'}:
        return False
    else:
        raise


def has_cooling_system(bpr):
    """
    determines whether a building has a cooling system installed or not

    :param bpr: building properties row object
    :rtype: bool
    """

    if bpr.hvac['type_cs'] in {'T1', 'T2', 'T3'}:
        return True
    elif bpr.hvac['type_cs'] in {'T0'}:
        return False
    else:
        raise


def heating_system_is_ac(bpr):
    """
    determines whether a building's heating system is ac or not

    :param bpr: building properties row object

    :rtype: bool
    """

    if bpr.hvac['type_hs'] in {'T3'}:  # central ac
        return True
    elif bpr.hvac['type_hs'] in {'T0', 'T1', 'T2', 'T4'}:
        return False
    else:
        print('Error: Unknown heating system')
        return False


def cooling_system_is_ac(bpr):
    """
    determines whether a building's heating system is ac or not

    :param: bpr: building properties row object

    :rtype: bool
    """

    if bpr.hvac['type_cs'] in {'T2', 'T3'}:  # mini-split ac and central ac
        return True
    elif bpr.hvac['type_cs'] in {'T0', 'T1'}:
        return Fal
    else:
        print('Error: Unknown cooling system')
        return False


def is_active_heating_system(bpr, tsd, t):

    # check for heating system in building
    # check for heating season
    # check for heating demand
    if helpers.is_heatingseason_hoy(t) \
            and has_heating_system(bpr) \
            and rc_model_SIA.has_heating_demand(bpr, tsd, t):

        return True
    else:
        return False


def is_active_cooling_system(bpr, tsd, t):

    # check for cooling system in building
    # check for cooling season
    # check for cooling demand
    if helpers.is_coolingseason_hoy(t) \
            and has_cooling_system(bpr) \
            and tsd['T_ext'][t] >= tsd['ta_cs_set'][t] \
            and rc_model_SIA.has_cooling_demand(bpr, tsd, t):

        return True
    else:
        return False
