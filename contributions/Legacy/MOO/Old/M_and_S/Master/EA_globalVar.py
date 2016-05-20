"""
===========================
Evolutionary algorithm Data
===========================

"""

buildListFile = "BuildingsName.csv"

HeatfeatureList = ["T_return_DH_result", "T_supply_DH_result", "mdot_DH_result"]
# Warning, when extracting from DataFrame, the columns keep the same order
# as in the original file

nDay = 365

# Number of possible generation units
nHeat = 8
nHR = 2
nSolar = 3
nCool = 3

# CO2 boundaries
CO2Min = 0.3
CO2Max = 0.6

MaxSizeCP_Dico = {
    "Furnace":10E6,
    "HP":20.0E6,
    "CC":35E6,
    "Boiler":210E6
    }

MaxSizeDP_Dico = {
    "FC":10E3,
    "Boiler":320E3,
    "GHP":30.5E3
    }

margin = 0.10
nInd = 10









