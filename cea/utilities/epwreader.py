"""
===========================
Energyplus file reader
===========================
File history and credits:
C. Miller script development               10.08.14
J. A. Fonseca  adaptation for CEA tool      18.05.16
J. A. Fonseca  adding sky temperature Epuls model     20.10.16
"""
import pandas as pd

import cea.inputlocator
import cea.globalvar as globalvar
import numpy as np
gv = globalvar.GlobalVariables()


__author__ = "Clayton Miller"
__copyright__ = "Copyright 2014, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Clayton Miller", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def epw_reader(weather_path):

    epw_labels = ['year', 'month', 'day', 'hour', 'minute', 'datasource', 'drybulb_C', 'dewpoint_C', 'relhum_percent',
                       'atmos_Pa', 'exthorrad_Whm2', 'extdirrad_Whm2', 'horirsky_Whm2', 'glohorrad_Whm2',
                       'dirnorrad_Whm2', 'difhorrad_Whm2', 'glohorillum_lux', 'dirnorillum_lux','difhorillum_lux',
                       'zenlum_lux', 'winddir_deg', 'windspd_ms', 'totskycvr_tenths', 'opaqskycvr_tenths', 'visibility_km',
                       'ceiling_hgt_m', 'presweathobs', 'presweathcodes', 'precip_wtr_mm', 'aerosol_opt_thousandths',
                       'snowdepth_cm', 'days_last_snow', 'Albedo', 'liq_precip_depth_mm', 'liq_precip_rate_Hour']

    result = pd.read_csv(weather_path, skiprows=8, header=None, names=epw_labels).drop('datasource', axis=1)
    result['dayofyear'] = pd.date_range('1/1/2010', periods=8760, freq='H').dayofyear
    result['ratio_diffhout'] = result['difhorrad_Whm2']/result['glohorrad_Whm2']
    result['skycover'] = result['ratio_diffhout'].fillna(1)
    result['skytemp_C']  = np.vectorize(calc_skytemp)(result['drybulb_C'], result['dewpoint_C'], result['skycover'] )

    return result

def calc_skytemp(Tdrybulb, Tdewpoint, N):
    sky_e = (0.787 + 0.764 *((Tdewpoint+273)/273))*1+0.0224*N+0.0035*N**2+0.00025*N**3
    hor_IR = sky_e * gv.blotzman * (Tdrybulb+273)**4
    sky_T = ((hor_IR/gv.blotzman)**0.25)-273

    return sky_T # sky temperature in C

def test_reader():

    locator = cea.inputlocator.InputLocator(r'C:\reference-case\baseline')
    # for the interface, the user should pick a file out of of those in ...DB/Weather/...
    weather_path = locator.get_default_weather()
    epw_reader(weather_path=weather_path)

if __name__ == '__main__':
    test_reader()


