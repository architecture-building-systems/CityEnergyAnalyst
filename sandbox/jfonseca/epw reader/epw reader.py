"""
===========================
Energyplus file reader
===========================
File history and credits:
C. Miller script development               10.08.14
J. A. Fonseca  adaptation for CEA tool     18.05.16

"""
import pandas as pd

def epw_reader(file_path):

    EPWColumnLabels = ['year', 'month', 'day', 'hour', 'minute', 'datasource', 'drybulb_C', 'dewpoint_C', 'relhum_%',
                       'atmos_Pa', 'exthorrad_Whm2', 'extdirrad_Whm2', 'horirsky_Whm2', 'glohorrad_Whm2',
                       'dirnorrad_Whm2', 'difhorrad_Whm2', 'glohorillum_lux', 'dirnorillum_lux','difhorillum_lux',
                       'zenlum_lux', 'winddir_deg', 'windspd_ms', 'totskycvr_tenths', 'opaqskycvr_tenths', 'visibility_km',
                       'ceiling_hgt_m', 'presweathobs', 'presweathcodes', 'precip_wtr_mm', 'aerosol_opt_thousandths',
                       'snowdepth_cm', 'days_last_snow', 'Albedo', 'liq_precip_depth_mm', 'liq_precip_rate_Hour']

    result = pd.read_csv(file_path, skiprows=8, header=None, names=EPWColumnLabels).drop('datasource', axis=1)

    return result

def test_reader():

    file_path = r'C:\Users\JF\Documents\CEAforArcGIS\cea\db\Weather data/CHE_Geneva.067000_IWEC.epw'
    epw_reader(file_path)

if __name__ == '__main__':
    test_reader()


