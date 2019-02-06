:orphan:

Variable Naming in CEA
======================

This is a guide on how to name variables in CEA. Please do read / print before adding new varaibles to the code.

Demand Side Load Nomenclature
-----------------------------

The variables that fall under this classification follow the syntax provided below:

**(LOAD TYPE)(LOAD)_(LOSSES)_(UNITS)**

The different values these parameters can take are enlisted below. The list is not exhaustive but will serve as a guide

**Load Type:**

+----+------------+
| Q  | Thermal    |
+----+------------+
| E  | Electrical |
+----+------------+


**Load**

+----------+----------------------+
| al       | appliances           |
+----------+----------------------+
| cdata    | data cooling         |
+----------+----------------------+
| cs       | space cooling        |
+----------+----------------------+
| cre      | refrigeration        |
+----------+----------------------+
| hs       | space heating        |
+----------+----------------------+
| l        | lighting             |
+----------+----------------------+
| pro      | industrial processes |
+----------+----------------------+
| T        | total                |
+----------+----------------------+
| ww       | hot water            |
+----------+----------------------+


**Losses**

+------+---------------------------------------------------------------------------+
| sys  | including losses (emission, distribution and storage inside the building) |
+------+---------------------------------------------------------------------------+
| ''   | if not used, then it is an end-use demand without losses                  |
+------+---------------------------------------------------------------------------+


**Units**

+--------+-------------------------+
| W      | Watt                    |
+--------+-------------------------+
| kWh    | kilo Watt hour          |
+--------+-------------------------+
| MWhyr  | Mega Watt hour per year |
+--------+-------------------------+

**For Example:**

``El_sys_W``        :   End-use demand of electricity required for lighting including system losses (in Watts)

``El_W``            :   End-use demand of electricity required for lighting without system losses (in Watts)

``ET_sys_MWhyr``    :   Total end-use demand of electricity required including system losses (in MWh per year)


Supply Side Load Nomenclature
-----------------------------

The variables that fall under this classification follow the syntax provided below:

**(LOAD TYPE)(LOAD)_(GENERATION UNIT)_(LOAD DIRECTION)_(UNITS)**

The different values these parameters can take are enlisted below. The list is not exhaustive but will serve as a guide


**Load Type:**

+----+------------+
| Q  | Thermal    |
+----+------------+
| E  | Electrical |
+----+------------+


**Load**

+----------+----------------------+
| al       | appliances           |
+----------+----------------------+
| cdata    | data cooling         |
+----------+----------------------+
| cs       | space cooling        |
+----------+----------------------+
| cre      | refrigeration        |
+----------+----------------------+
| hs       | space heating        |
+----------+----------------------+
| l        | lighting             |
+----------+----------------------+
| pro      | industrial processes |
+----------+----------------------+
| T        | total                |
+----------+----------------------+
| ww       | hot water            |
+----------+----------------------+


**Generation Unit**

+--------------+----------------------------+
| PV           | Photovoltaic               |
+--------------+----------------------------+
| PVT          | Photovoltaic Thermal       |
+--------------+----------------------------+
| SC           | Solar Collector            |
+--------------+----------------------------+
| CCGT         | Combined Cycle Gas Turbine |
+--------------+----------------------------+
| FC           | Fuel Cell                  |
+--------------+----------------------------+
| GSHP         | Ground Source Heat Pump    |
+--------------+----------------------------+
| BASEBOILER   | Base Boiler                |
+--------------+----------------------------+
| PEAKBOILER   | Peak Boiler                |
+--------------+----------------------------+
| BACKUPBOILER | Backup Boiler              |
+--------------+----------------------------+
| VCC          | Vapor Compression Chiller  |
+--------------+----------------------------+


**Load Direction**

+--------+--------------------+
| GRID   | to the local grid  |
+--------+--------------------+
| DIRECT | to the direct load |
+--------+--------------------+


**Units**

+--------+-------------------------+
| W      | Watt                    |
+--------+-------------------------+
| kWh    | kilo Watt hour          |
+--------+-------------------------+
| MWhyr  | Mega Watt hour per year |
+--------+-------------------------+

**For Example:**

``Qww_PVT_DIRECT_MWhyr``    :   Heat generated by PVT supplied to the directload of hot water demand (MWhyr)

``ET_PV_GRID_MWhyr``        :   Total electricity generated by PV which is supplied to the local power grid (MWhyr)


Supply Side Cost Nomenclature
-----------------------------

The variables that fall under this classification follow the syntax provided below:

**(COSTS TYPE 1)_(COSTS TYPE 2)_(COSTS TYPE 3)_(GENERATION UNIT)_(UNITS)**

The different values these parameters can take are enlisted below. The list is not exhaustive but will serve as a guide


**Costs Type 1**

+-------+-------------------------+
| Capex | Capital Expenditure     |
+-------+-------------------------+
| Opex  | Operational Expenditure |
+-------+-------------------------+


**Costs Type 2**

+---+------------+
| T | Total      |
+---+------------+
| A | Annualized |
+---+------------+


**Costs Type 3**

+-----+----------+
| Var | Variable |
+-----+----------+
| Fix | Fixed    |
+-----+----------+


**Generation Unit**

+--------------+----------------------------+
| PV           | Photovoltaic               |
+--------------+----------------------------+
| PVT          | Photovoltaic Thermal       |
+--------------+----------------------------+
| SC           | Solar Collector            |
+--------------+----------------------------+
| CCGT         | Combined Cycle Gas Turbine |
+--------------+----------------------------+
| FC           | Fuel Cell                  |
+--------------+----------------------------+
| GSHP         | Ground Source Heat Pump    |
+--------------+----------------------------+
| BASEBOILER   | Base Boiler                |
+--------------+----------------------------+
| PEAKBOILER   | Peak Boiler                |
+--------------+----------------------------+
| BACKUPBOILER | Backup Boiler              |
+--------------+----------------------------+
| VCC          | Vapor Compression Chiller  |
+--------------+----------------------------+


**Units**

+-------+--------------------------+
| USD   | US Dollar (2015)         |
+-------+--------------------------+
| MUSD  | Million US Dollar (2015) |
+-------+--------------------------+

**For Example:**

``Capex_A_Fix_CCGT_MUSD``   :   Annualized CAPEX (fixed component) for CCGT equipment (in million USD)

``Opex_T_Var_FC_USD``       :   Total OPEX (variable component) of FC equipment (in USD)


Supply Side Fuel Nomenclature
-----------------------------

The variables that fall under this classification follow the syntax provided below:

**(FUEL TYPE)_(FUEL DIRECTION)_(GENERATION UNIT)_(UNITS)**

The different values these parameters can take are enlisted below. The list is not exhaustive but will serve as a guide

**Fuel Type**

+------+-------------+
| NG   | Natural Gas |
+------+-------------+
| Wood | Wood        |
+------+-------------+

**Fuel Direction**

+------+----------------------------------------------+
| used | Fuel is used by the generation unit          |
+------+----------------------------------------------+
| gen  | resource is generated by the generation unit |
+------+----------------------------------------------+

**Generation Unit**

+--------------+----------------------------+
| PV           | Photovoltaic               |
+--------------+----------------------------+
| PVT          | Photovoltaic Thermal       |
+--------------+----------------------------+
| SC           | Solar Collector            |
+--------------+----------------------------+
| CCGT         | Combined Cycle Gas Turbine |
+--------------+----------------------------+
| FC           | Fuel Cell                  |
+--------------+----------------------------+
| GSHP         | Ground Source Heat Pump    |
+--------------+----------------------------+
| BASEBOILER   | Base Boiler                |
+--------------+----------------------------+
| PEAKBOILER   | Peak Boiler                |
+--------------+----------------------------+
| BACKUPBOILER | Backup Boiler              |
+--------------+----------------------------+
| VCC          | Vapor Compression Chiller  |
+--------------+----------------------------+

**Units**

+--------+-------------------------+
| W      | Watt                    |
+--------+-------------------------+
| kWh    | kilo Watt hour          |
+--------+-------------------------+
| MWhyr  | Mega Watt hour per year |
+--------+-------------------------+

**For Example:**

``NG_used_HPSew_W``         :   Natural gas used by sewage heat pump (in Watts)

``Wood_used_Furnace_W``     :   Wood used by Furnace (in Watts)

Supply Side Emissions Nomenclature
----------------------------------

**(LCA TYPE)_(GENERATION UNIT)_(UNITS)**

**LCA Type**

+-----+---------------------------+
| GHG | Green house gas emissions |
+-----+---------------------------+
| PEN | Primary Energy            |
+-----+---------------------------+


**Generation Unit**

+--------------+----------------------------+
| PV           | Photovoltaic               |
+--------------+----------------------------+
| PVT          | Photovoltaic Thermal       |
+--------------+----------------------------+
| SC           | Solar Collector            |
+--------------+----------------------------+
| CCGT         | Combined Cycle Gas Turbine |
+--------------+----------------------------+
| FC           | Fuel Cell                  |
+--------------+----------------------------+
| GSHP         | Ground Source Heat Pump    |
+--------------+----------------------------+
| BASEBOILER   | Base Boiler                |
+--------------+----------------------------+
| PEAKBOILER   | Peak Boiler                |
+--------------+----------------------------+
| BACKUPBOILER | Backup Boiler              |
+--------------+----------------------------+
| VCC          | Vapor Compression Chiller  |
+--------------+----------------------------+

**Units**

+--------+-------------------------------+
| tonCO2 | tons of CO2 equivalent        |
+--------+-------------------------------+
| MJoil  | Mega Joules of oil equivalent |
+--------+-------------------------------+
| GJoil  | Giga Joules of oil equivalent |
+--------+-------------------------------+

**For Example:**


``GHG_PVT_tonCO2``          :   Green house gas emissions of PVT (in tons of CO2 equivalent)

``PEN_PV_MJoil``            :   Primary Energy corresponding to PV (in Mega Joules of Oil equivalent)


