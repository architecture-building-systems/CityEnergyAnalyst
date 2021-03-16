import time

def get_seconds(d):
    """
    Convert to seconds from the epoch
    """
    date_fmt="%Y%m%d%H%M"
    return time.mktime(time.strptime(d,date_fmt)) # to seconds from the epoch

# Configure the following variables

# for b35 NMINUTES has to be 15,30 or 60
NMINUTES=60 # number of minutes in each interval  (10,20,30,60,120,etc)
from_date="201001010000"
to_date="201101010000"

# Resolution weather files in minutes
NMINUTES_WEATHER_FILE = 60
NPERIODS_WEATHER_FILE = int(NMINUTES/NMINUTES_WEATHER_FILE) # resolution of 10 mins for temperature and solar radiation files

NMINUTES_B35_FILE = 15
NPERIODS_B35_FILE = int(NMINUTES/NMINUTES_B35_FILE)

##### this variables MUST NOT be configured #####
NPERIODS_HOUR=int(60/NMINUTES) ## number of periods in one hour
NPERIODS_DAY=NPERIODS_HOUR*24

# W to kWh constant
W2kWh = 1./(1000.0*NPERIODS_HOUR)
NPERIODS_HOUR_WEATHER_FILE=int(60/NMINUTES_WEATHER_FILE) ## number of periods in one hour
W2kWh_radfile = 1./(1000.0*NPERIODS_HOUR_WEATHER_FILE)
START_DATE=get_seconds(from_date)
END_DATE=get_seconds(to_date)

#quarter hour counter
NPERIODS=int((END_DATE-START_DATE)/(60*NMINUTES))
NDAYS=int((END_DATE-START_DATE)/(60*24*60))


# Constants
## Physical constants
Cp_water=4.1855 #[kJ/(kg.K)]
Cp_water_kWh=Cp_water/(3600.) # [kWh/(kg.K)]
Cp_air=1.012 # [kJ/(kg.K)]
Cp_air_kWh=Cp_air/3600. #[kWh/(Kg.K)]
rho_air=1.225 # [kg/m3]
DeltaTemp_DHW=35 #[C] DeltaT
## for the HDD calculation
HDD_targetTemp=21  # [C]
HDD_heatingTemp=14 # [C]
HDD_highTemp=20 # [C]
HDD_lowTemp=14 # [C]  -> averaged over 2-day
CDD_coolingTemp=26 # [C]
CDD_targetTemp=24 # [C]
## Ventilation
Air_InputTemp = 21
## recovering coefficient Waermerueckgewinnung
recovering_coeff=0.75 # [0.70,0.75,0.8]
## infiltration rate and volume rate from SIA 2024 page 15
Vinfl=0.1 #[m^3/m^2*h]
volume_rate_day=30 #[m^3/P]  This volume rate is per hour and therefore has to be diveded by NPERIODS_HOUR
volume_rate_night=15 #[m^3/P]  This volume rate is per hour and therefore has to be diveded by NPERIODS_HOUR