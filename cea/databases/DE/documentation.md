# German Building Stock Database

This is the accompanying documentation to the German building stock database developed for the open-source software CityEnergy Analyst (CEA).

## Table of Contents

- [German Building Stock Database](#german-building-stock-database)
  - [Table of Contents](#table-of-contents)
  - [Description](#description)
  - [Abbreviations](#abbreviations)
  - [Archetypes](#archetypes)
    - [CONSTRUCTION\_STANDARD](#construction_standard)
      - [STANDARD\_DEFINITION](#standard_definition)
      - [ENVELOPE\_ASSEMBLIES](#envelope_assemblies)
      - [HVAC\_ASSMEBLIES](#hvac_assmeblies)
      - [SUPPLY\_ASSEMBLIES](#supply_assemblies)
    - [use\_types](#use_types)
      - [Residential types](#residential-types)
        - [Use type properties - internal loads](#use-type-properties---internal-loads)
        - [Use type properties - indoor comfort](#use-type-properties---indoor-comfort)
        - [SCHEDULES](#schedules)
      - [Non-Residential types](#non-residential-types)
  - [Assemblies](#assemblies)
    - [ENVELOPE](#envelope)
      - [CONSTRUCTION](#construction)
      - [TIGHTNESS](#tightness)
      - [ROOF](#roof)
      - [WALL](#wall)
      - [FLOOR](#floor)
      - [WINDOW](#window)
      - [SHADING](#shading)
    - [SUPPLY](#supply)
      - [ELECTRICITY](#electricity)
      - [HEATING](#heating)
      - [HOT\_WATER](#hot_water)
      - [COOLING](#cooling)
  - [Components](#components)
    - [CONVERSION](#conversion)
    - [DISTRIBUTION](#distribution)
    - [FEEDSTOCKS / ENERGY\_CARRIERS](#feedstocks--energy_carriers)
  - [Contribute](#contribute)
  - [Authors](#authors)
  - [References](#references)

## Description

The basic structure of the database is equivalent to the default Switzerland database in CEA.
This documentation follows the same hierarchical organization as the input files do, starting from the highest "archetypes" level, until the most granular "components" level.

Please refer to the CEA github repository for questions regarding the usage
of any database, including this one. If you do find the database useful, please cite the
following submitted conference paper:

> Ceruti, A., Geske, M., Hartmann, U., Spliethoff, H., Voelker, C. (2024). From Building to District: Accelerating Urban Building Energy Modeling with an Open-Source Database for Germany. BauSIM 2024, Austria. [DOI: 10.26868/29761662.2024.22]

The reference will be updated as soon as it underwent the review process and has been published.

## Abbreviations

- DE: Germany
- CH: Switzerland
- CEA: CityEnergyAnalyst
- SFH: single family house
- MFH: multi family house
- TH: terraced home
- AB: apartment block
- NR: normal renovation as defined in the IWU EPISCOPE project (implemented in TABULA typology)
- AR: advanced renovation as defined in EPISCOPE
- NWG: Nicht-Wohngebäude (non residential building)
- WW: domestic hot water
- IWU: Institut Wohnen und Umwelt
- BMVBS: Bundesministerium für Verkehr, Bau und Stadtentwicklung; now called Bundesministerium für Digitales und Verkehr.
- GDR: German Democratic Republic ("East Germany" before unification)

## Archetypes

The naming convention for the buildings is defined as follows:

`Building Type(_Category)_Age(_Refurbishment status)`

For example, for a multi-family home, with normal refurbishment from the 80s: `MFH_H_NR`.
For a commercial building destined to services with a generalized profile: `NWG_G1_A`.

The Category is included only for non-residential buildings for the IWU typology,
while the Refurbishment status is only available for residential buildings. An additional
term `-EAST` designates the eastern german (former GDR) buildings.

### CONSTRUCTION_STANDARD

#### STANDARD_DEFINITION

| Parameter   | Description   | Method  |
|---   |---   |---  |
| `STANDARD`   | building archetype as defined in STANDARD_DEFINITION  | One for each TABULA[^tab] building archetype in Germany or non residential typology from either BMVBS[^BMVBS] or IWU[^IWU-NW-data][^IWU-NW-paper] |
| `Description`  | Description of STANDARD | As defined in TABULA DE, BMBVS or IWU |
| `YEAR_START` | Starting year of construction | As defined in TABULA DE, BMBVS or IWU |
| `YEAR_END`  | Last year of construction | As defined in TABULA DE, BMBVS or IWU |

#### ENVELOPE_ASSEMBLIES

Source for descriptions of the parameters: [^cea-desc].

| Parameter           | Description                                                                                                | Method                                                                                                                                                                            |
|---------------------|------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `STANDARD`          | building archetype name                                                                                    | One for each TABULA, EPISCOPE and IWU building archetype in Germany (See abbreviations above)                                                                                     |
| `type_cons`         | Type of construction assembly (relates to "code" in ENVELOPE assemblies)                                   | Standard values as defined in p. 8 of the common calculation method of TABULA[^tab-com] (and unit conversion to CEA)                                                              |
| `type_leak`         | Tightness level assembly (relates to "code" in ENVELOPE assemblies)                                        | According to values defined in the common calculation method of TABULA[^tab-com] p.13 and each building typology. For IWU and BMVBS it was assumed medium or low depending on age |
| `type_win`          | Window assembly (relates to "code" in ENVELOPE assemblies)                                                 | Values depending on renovation status defined in TABULA with additional assumptions                                                                                               |
| `type_roof`         | Roof construction assembly (relates to "code" in ENVELOPE assemblies)                                      | Values for all building typologies defined in TABULA, BMBVS or IWU, and assumptions for missing values                                                                            |
| `type_part`         | Internal partitions construction assembly (relates to "code" in ENVELOPE assemblies)                       | One standard assumption for all                                                                                                                                                   |
| `type_wall`         | External wall construction assembly (relates to "code" in ENVELOPE assemblies)                             | Values for all building typologies defined in TABULA, and assumptions for missing values                                                                                          |
| `type_floor`        | Internal floor construction assembly (relates to "code" in ENVELOPE assemblies)                            | Values for all building typologies defined in TABULA                                                                                                                              |
| `type_base`         | Internal floor construction assembly (relates to "code" in ENVELOPE assemblies)                            | Assumed equal to floor insulation of each building typology for TABULA DE (not measured)                                                                                          |
| `type_shade`        | Shading system assembly (relates to "code" in ENVELOPE assemblies)                                         | Assumed as vertical window for all typologies (TABULA p. 8 TABULA common calculation method[^tab-com])                                                                            |
| `Es`                | Fraction of gross floor area with energy demands                                                           | Default tabula value = 0.85                                                                                                                                                       |
| `Hs`                | Fraction of gross floor area air-conditioned                                                               | Equal to Es, TABULA assumption                                                                                                                                                    |
| `occupied_bg` | True if floors below ground are conditioned/occupied, False if not.                                        | Assumed False                                                                                                                                                                     |
| `Ns`                | Fraction of net gross floor area                                                                           | Assumption of 0.85                                                                                                                                                                |
| `void_deck`         | Number of floors (from the ground up) with an open envelope (default = 0, should be lower than floors_ag.) | 0                                                                                                                                                                                 |
| `wwr_[]`            | Window to wall ratio in facades directions                                                                 | Values for all building typologies defined in TABULA, calculated from facade, wall and window surfaces in IWU                                                                     |

#### HVAC_ASSMEBLIES

Used  standard values of CEA for all types. HVAC_HEATING_AS1 (90/70 radiators °C) or HVAC_HEATING_AS2 (70/55 °C) depending on TABULA typology and renovations tatus. Used HVAC_VENTILATION_AS2 or HVAC_VENTILATION_AS0 depending on EPISCOPE Advanced Reonvation scenario including heat recovery in the ventilation.

HVAC_COOLING_AS3, HVAC_HOTWATER_AS1, HVAC_CONTROLLER_AS1 used for all types. 

Heating starting and ending dates are assumed all year and no cooling demands (heat_starts = 01|09 and heat_ends = 31|08; cool_starts and cool_ends = 00|00). Alternatively, the "Mietrecht" (tenancy law) in Germany requires heating from 01|10 until 30|04.

#### SUPPLY_ASSEMBLIES

The categories defined in SUPPLY are mapped to the construction standards in the SUPPLY_ASSEMBLIES file. The technologies were assigned manually with a corresponding TABULA technology specified in the TABULA webtool (https://webtool.building-typology.eu/#bm)[https://webtool.building-typology.eu/#bm]. The efficiencies are not consistent with reported TABULA values, especially for the hot water supply.

| Parameter   | Description   | Method  |
|---   |---   |---  |
| `type_cs` |  Type of cooling supply assembly (refers to “code” in SUPPLY assemblies) |  Selection is made based on the defined standards for the respective construction or renovation year |
| `type_hs` |  Type of heating supply assembly (refers to “code” in SUPPLY assemblies) |  Selection is made based on the defined standards for the respective construction or renovation year |
| `type_dhw` |  Type of hot water supply assembly (refers to “code” in SUPPLY assemblies) |  Selection is made based on the defined standards for the respective construction or renovation year |
| `type_el` |  Type of electrical supply assembly (refers to “code” in SUPPLY assemblies) |  Selection is made based on the defined standards for the respective construction or renovation year |

#### MFH, MFH-EAST, AB, AB-EAST, SFH, TH

The advanced renovation scenarios are assumed to be only high efficiency gas boilers + solar thermal flatplate collectors instead of gas boilers in combination with solar thermal (solar fractioin from 40 (NR) to 60% (AR)), heat recovery systems and sometimes micro-CHPs. Currently, only one hotwater supply technology can be selected - it was assumed to be solar thermal flatplate collectors if specified in the TABULA scenarios independently of the solar fraction.

#### NWG

Categories A and B of all types assumed to be low temperature gas boilers. Age C buildings are assumed to have condensing gas boilers. 


### use_types

The calculation basis for the occupancy in CEA is structured according to the Swiss standard SIA. In contrast, the German standard lacks such a data basis, particularly for energy modelling on an hourly basis.
DIN EN 18599 describes various, energetic parameters for many usages, but in the context of simplified calculation based on a simplified monthly balancing procedure taking into account the different thermal zones of a building. Due to this structural differences the values cannot be directly transferred to CEA. Based on this and other regulation we modified the Swiss occupancy profiles for residential usage in single and multi family houses.
DIN EN 16789-1:2019 presents indoor environmental input parameters for design and assessment of energy performance of buildings and includes information on indoor air quality, thermal environment, lighting and acoustics.

#### Residential types

Cooling is always equal to CH database. The naming convention is the same as the CH database. For residential profiles:

- `SINGLE_RES`: Single family home
- `MULTI_RES`: Multi family home

#### Non-Residential types

In the current status, there are some non-residential use types included. There is only a very heterogeneous data basis for non-residential buildings in Germany:

- DIN/TS 18599 (e.g. Teil 13: Tabulation method for non-residential buildings): Also describes many occupancy profiles, but against the background of simplified calculation in the course of energy consulting. In this case, a simplified monthly balance procedure is usually used. However, the different thermal zones of a building are taken into account. For this reason, the values cannot be transferred directly to CEA.
- Standardlastprofile des BDEW (in English: Standard load profiles): These standardized load profiles contain the usual energy load patterns in Germany. They are often used for analyzing/monitoring the energy supply. However, they are based on the consumption of the German grid and are not intended as input data for a reduced order model.

So, if the data is available in DIN 18599-13, this was added to the USE_TYPE_PROPERTIES excel; otherwise, it was assumed to be equal to CH defaults. 

#### Use type properties - internal loads

| Parameter   | Description   | Method  |
|---   |---   |---  |
| `Occ_m2P` | Occupancy density (refers to “code”) | According to Sagner: 48 m2 per person for house owner (SFH)  and 35m2 per Person in rented flats (MFH)  |
| `El_Wm2` |  Peak specific electrical load due to artificial lighting (refers to “code”)| DIN V 18599-4 Anhang B (Abbildung B.12) =  6,4 W/m²  |
| `Vw_ldp`  | Peak specific fresh water consumption (refers to “code”) | average water consumption for Germany [^BDEW] |
| `Vww_ldp` | Peak specific hot water consumption (refers to “code”)| 10% of `Vww` (educated guess) |

#### Use type properties - indoor comfort

| Parameter   | Description   | Method  |
|---   |---   |---  |
| `Tcs_set_C` |   Setpoint temperature for cooling system (refers to "code")  |  DIN EN 16798-1:2022-03 Tab.NA.3 Höchstwert für Kühlung in der Sommerperiode Wohnen Kat. II : 26°C AND DIN V 18599-10:2018-10 Tab. 4 Auslegung Kühlfall|
| `Tcs_setb_C` |  Setback point of temperature for cooling system (refers to "code")  | DIN V 18599-10:2018-09 Tab. 4 |
| `Ths_set_C` |   Setpoint temperature for heating system (refers to "code") | DIN EN 16798-1:2022-03 Tab.NA.3  Wohnen Kat. I: 20°C AND DIN V 18599-10:2018-10 Tab. 4 Auslegungstemperatur Heizfall and DIN EN 18599-13 Tab. 8 if available, CH defaults otherwise |
| `Ths_setb_C` |  Setback point of temperature for heating system  (refers to "code")  |  DIN V 18599-10:2018-10 Tab. 4 Temperaturabsenkung Reduzierter Betrieb = 4 K. Example: 20 °C ->16 °C |
| `Ve_lsp` | Minimum outdoor air ventilation rate per person for Air Quality (refers to "code")  |  DIN EN 16798-1:2022-03 Tab.NA.6 Kat. II - I  (erhöht auf Grdl. VDI Empfehlung zu 30 m³/h |

##### SCHEDULES

| Parameter   | Method  |
|---   |---   |
| OCCUPANCY | modified according to  DIN EN 16798 and DIN18599 for Residential. Non residential assumed equal to CH. |
| APPLIENCES | 0.5 as baseline, others correlating with occupancy  |  
| LIGHTING | starting at 7 am, correlating with occupancy, but modified  |  
| WATER | starting at 7 am, correlating with occupancy  |  
| SETPOINT | DIN V 18599-10:2018 Tab. 4 Nutzungszeit von 6:00 - 23:00 |  
| SETBACK | if not SETPOINT|  

#### Internal Load Calculations

- Water usage School with shower: 250 Wh/m2/d $\times$ 3 m2/p / 23.28 Wh/l at 20 K temperature difference = 32.22 l/d/p [18599-13].
- Water usage School without shower: 10.95 l/d/p [18599-13].
- Assumed cold water usage equal to warmwater usage in School.
- Warm water usage in office assumed equal to 2.5 l/d/p according to paper 'Fuentes, Elena, L. Arce, and Jaume Salom. "A review of domestic hot water consumption profiles for application in systems and buildings energy performance analysis." Renewable and Sustainable Energy Reviews 81 (2018): 1530-1547.
- Restaurant assumed to be equal to: "Bürogebäude mit
Gaststätte" of DIN 18599-13 -> 1500*1.2/23.28=77 l/d/p, cold water assumed equal.
- Hotel left equal to CH.
- Library: 30*5/23.28=6.44 l/d/p.

## Assemblies

### ENVELOPE

The current renovation scenarios are entirely based on the IWU EPISCOPE project (normal or advanced). If more detailed scenarios are needed, the relevant construction standards for Germany (i.e. Wärmeschutzverordnung WSchW, Energieeinsparverordnung EnEV) need to be implemented in the database, refer to [^EnEV].[^WSchV]. The Service life parameter is filled with the default values of the
CH database.

#### CONSTRUCTION

| Parameter   | Description   | Method  |
|---   |---   |---  |
| `Descriptio`  | Description of code | |
| `code` | Assembly code used used in ENVELOPE_ASSEMBLIES |  |
| `Cm_Af` | Internal heat capacity per unit of area [J/K·m2] | Standard value used for TABULA buildings and unit conversion from 45 Wh/m2·K to J/m2·K |

#### TIGHTNESS

| Parameter   | Description   | Method  |
|---   |---   |---  |
| `Description`  | Description of code | |
| `code` | Assembly code used used in ENVELOPE_ASSEMBLIES |  |
| `n50` | Air tightness at 50 Pa [h^-1] | Recalculated with reference values provided in TABULA common calculation method p. 13 [^tab-com] |

#### ROOF

| Parameter   | Description   | Method  |
|---   |---   |---  |
| `Description`  | Description of code |  |
| `code` | Assembly code used used in ENVELOPE_ASSEMBLIES | Naming convention depending on typology and renovation status (see Abbreviations) |
| `U_roof` | U value of the floor construction [W/m2K] | Depending on archetype, typology and renovation status value |
| `a_roof` | Solar absorption coefficient. Defined according to ISO 13790 | Assumption of standard value from CEA CH database |
| `e_roof` | Emissivity of external surface. Defined according to ISO 13790. | Assumption of standard value from CEA CH database |
| `r_roof` | Reflectance in the Red spectrum. Defined according Radiance. (long-wave) | Assumption of standard value from CEA CH database |
| `GHG_roof_kgCO2m2` | Embodied emissions per m2 of roof.(entire building life cycle) | Assumption of standard value from CEA CH database |
| `Service_Life_roof` | Service life of the component in years (entire building life cycle) | Assumption of standard value from CEA CH database |

#### WALL

| Parameter   | Description   | Method  |
|---   |---   |---  |
| `Description`  | Description of code |  |
| `code` | Assembly code used used in ENVELOPE_ASSEMBLIES | Naming convention depending on typology and renovation status (see Abbreviations) |
| `U_wall` | U value of the wall construction [W/m2K] | Depending on archetype, typology and renovation status value |
| `a_wall` | Solar absorption coefficient. Defined according to ISO 13790 | Assumption of standard value from CH database |
| `e_wall` | Emissivity of external surface. Defined according to ISO 13790. | Assumption of standard value from CH database |
| `r_wall` | Reflectance in the Red spectrum. Defined according Radiance. (long-wave) | Assumption of standard value from CH database |
| `GHG_wall_kgCO2m2` | Embodied emissions per m2 of roof.(entire building life cycle) | Assumption of standard value from CH database |
| `Service_Life_wall` | Service life of the component in years (entire building life cycle) | Assumption of standard value from CEA CH database |

#### FLOOR

| Parameter   | Description   | Method  |
|---   |---   |---  |
| `Description`  | Description of code |  |
| `code` | Assembly code used used in ENVELOPE_ASSEMBLIES | Naming convention depending on typology and renovation status (see Abbreviations) |
| `U_base` | U value of the floor construction [W/m2K] | Depending on archetype, typology and renovation status value or assumed equal to floor for TABULA archetypes |
| `GHG_floor_kgCO2m2` | Embodied emissions per m2 of roof.(entire building life cycle) | Assumption of standard value from CH database |
| `Service_Life_floor` | Service life of the component in years (entire building life cycle) | Assumption of standard value from CEA CH database |

#### WINDOW

| Parameter   | Description   | Method  |
|---   |---   |---  |
| `Description`  | Description of code |  |
| `code` | Assembly code used used in ENVELOPE_ASSEMBLIES | Naming convention depending on typology and renovation status (see Abbreviations) |
| `U_win` | U value of the window construction [W/m2K] | Depending on archetype, typology and renovation status value |
| `G_win`| Solar heat gain coefficient. Defined according to ISO 13790. | Assignment of standard values from CH database, depending on standard window type specified in TABULA; assumption for NWG since not included in archetype |
| `e_win` | Emissivity of external surface. Defined according to ISO 13790. | Assignment of standard values from CH database, depending on standard window type specified in TABULA; assumption for NWG since not included in archetype |
| `F_F` | Window frame fraction coefficient. Defined according to ISO 13790. | Standard TABULA value (p. 8) of 0.3 |
| `GHG_win_kgCO2m2` | Embodied emissions per m2 of roof.(entire building life cycle) | Assumption of standard value from CH database |
| `Service_Life_win` | Service life of the component in years (entire building life cycle) | Assumption of standard value from CEA CH database |

#### SHADING

| Parameter   | Description   | Method  |
|---   |---   |---  |
| `Description`  | Description of code |  |
| `code` | Assembly code used used in ENVELOPE_ASSEMBLIES | Naming convention depending on shading type |
| `rf_sh` | Shading coefficient when shading device is active. Defined according to ISO 13790 | Typology standard values (0.6 vertical, 0.8 horizontal windows); Additional types defined from DIN 4108-2:2013-02 Tab. 7 with naming convention SHADING_MG[id] |

### SUPPLY

The heat technologies were adopted from CEA and adjusted according to the KEA technical catalog [^KEA] assuming that the following formula is still used in CEA:Investment costs = Investment costs per kW * efficiency of heat technology * thermal performance. The heating technologies were categorized into different power classes (10 kW, 50 kW, 100 kW). These are intended to reflect the capacities of a single-family house, a smaller, and a larger multi-family house. The selected capacity can be verified by calculating the heat demand in CEA. Contrary to the parameter labels, the costs are plotted in Euros for the reference year 2023!

The hot water and heating technologies types in CONSTRUCTION STANDARDS were assigned to TABULA standards with user assumptions consistently to the specified technology type in the TABULA webtool.


#### ELECTRICITY

| Parameter   | Description   | Method  |
|---   |---   |---  |
|CAPEX_USD2015kW | Capital costs per kW | Standard value from CH database |
|code | Code of electrical supply assembly | Standard value from CH database |
|Description | description | Standard value from CH database |
|efficiency | efficiency of the all in one system | Standard value from CH database |
|feedstock | feedstock used by the the all in one system (refers to the FEEDSTOCK database) | Standard value from CH database |
|IR_% | interest rate charged on the loan for the capital cost | Standard value from CH database |
|LT_yr | lifetime of assembly | Standard value from CH database |
|O&M_% | operation and maintenance cost factor (fraction of the investment cost) | Standard value from CH database |
|reference | reference | Standard value from CH database |
|scale | whether the all in one system is used at the building or the district scale | Standard value from CH database |

#### HEATING

| Parameter   | Description   | Method  |
|---   |---   |---  |
|CAPEX_USD2015kW | Capital costs per kW | Standard value from CH database that may have been adjusted with the sources in 'reference' |
|code | Code of heating supply assembly | Syntax from CH database |
|Description | description | Syntax from CH database |
|efficiency | efficiency of the all in one system | Standard value from CH database |
|feedstock | feedstock used by the the all in one system (refers to the FEEDSTOCK database) | Standard value from CH database |
|IR_% | interest rate charged on the loan for the capital cost | Standard value from CH database |
|LT_yr | lifetime of assembly | Standard value from CH database that may have been adjusted with the sources in 'reference' |
|O&M_% | operation and maintenance cost factor (fraction of the investment cost) | Standard value from CH database that may have been adjusted with the sources in 'reference' |
|reference | reference | Mainly KEA technical catalog |
|scale | whether the all in one system is used at the building or the district scale | Standard value from CH database |

#### HOT_WATER

| Parameter   | Description   | Method  |
|---   |---   |---  |
|CAPEX_USD2015kW | Capital costs per kW | Standard value from CH database that may have been adjusted with the sources in 'reference' |
|code | Code of hot water supply assembly | Syntax from CH database |
|Description | description | Syntax from CH database |
|efficiency | efficiency of the all in one system | Standard value from CH database that may have been adjusted with the sources in 'reference' |
|feedstock | feedstock used by the the all in one system (refers to the FEEDSTOCK database) | Standard value from CH database |
|IR_% | interest rate charged on the loan for the capital cost | Standard value from CH database |
|LT_yr | lifetime of assembly | Standard value from CH database that may have been adjusted with the sources in 'reference' |
|O&M_% | operation and maintenance cost factor (fraction of the investment cost) | Standard value from CH database that may have been adjusted with the sources in 'reference' |
|reference | reference | Mainly KEA technical catalog |
|scale | whether the all in one system is used at the building or the district scale | Standard value from CH database |

#### COOLING

The parameters have not been changed and correspond to the standard values from CEA for Switzerland.

| Parameter   | Description   | Method  |
|---   |---   |---  |
|CAPEX_USD2015kW | Capital costs per kW | Standard value from CH database |
|code | Code of cooling supply assembly | Standard value from CH database |
|Description | description | Standard value from CH database |
|efficiency | efficiency of the all in one system | Standard value from CH database |
|feedstock | feedstock used by the the all in one system (refers to the FEEDSTOCK database) | Standard value from CH database |
|IR_% | interest rate charged on the loan for the capital cost | Standard value from CH database |
|LT_yr | lifetime of assembly | Standard value from CH database |
|O&M_% | operation and maintenance cost factor (fraction of the investment cost) | Standard value from CH database |
|reference | reference | Standard value from CH database |
|scale | whether the all in one system is used at the building or the district scale | Standard value from CH database |

## Components

### CONVERSION

Added all necessary BOILER and HEATPUMP components defined in the TABULA standards with the [^KEA] dataset and converted to USD 2015 from EUR 2022. 

### DISTRIBUTION

No recent values than those in the CEA database were found, so the 2015 values were adjusted to the year 2023 using the USD inflation rate of 24.90% [^US].

| Parameter   | Description   | Method  |
|---   |---   |---  |
|Code | Standardized pipe size | |
|D_ext_m | external pipe diameter tolerance for the nominal diameter (DN)| Standard value from CH database |
|D_ins_m | maximum pipe diameter tolerance for the nominal diameter (DN) | Standard value from CH database |
|D_int_m | internal pipe diameter tolerance for the nominal diameter (DN) | Standard value from CH database |
|Inv_USD2015perm | Typical cost of investment for a given pipe diameter | Standard value from CH database |
|Pipe_DN | Nominal pipe diameter | Standard value from CH database |
|Vdot_max_m3s | maximum volumetric flow rate for the nominal diameter (DN) | Standard value from CH database |
|Vdot_min_m3s | minimum volumetric flow rate for the nominal diameter (DN) | Standard value from CH database |

### FEEDSTOCKS / ENERGY_CARRIERS

Current buying prices (beginning - mid 2023) for feedstocks or energy carriers were researched for Germany. The respective sources are referenced in the database. The emissions of electricity were not available in the specified unit within CEA. Therefore, the value was validated using the ratio of the emission factor in kg/kWh between Germany and Switzerland. Contrary to the parameter labels, the costs are plotted in Euros for the reference year 2023!

Hint: For calculating "district heating" feedstock, it's advisable to adjust the feedstock "Dry Biomass" as there is no section for district heating in CEA.

| Parameter   | Description   | Method  |
|---   |---   |---  |
|GHG_kgCO2MJ | Non-renewable Green House Gas Emissions factor | Different references for the feedstocks or energy carriers |
|hour | hour of a 24 hour day | Unchanged |
|Opex_var_buy_USD2015kWh | buying price | Different references for the feedstocks or energy carriers |
|Opex_var_sell_USD2015kWh  | selling price | not used, Approximation: equals buying price |
|reference | reference | Sources for feedstock prices and GHG Emissions |

## Contribute

Please feel free to use and contribute to this database by opening
a pull request on github detailing the made modifications in detail.

## Authors

In alphabetic order:

- Amedeo Ceruti
- Mara Geske
- Ulla Hartmann
- Urbano Tataranni

## References

[^tab]: Loga, Tobias, Britta Stein, and Nikolaus Diefenbach. "TABULA building typologies in 20 European countries—Making energy-related features of residential building stocks comparable." _Energy and Buildings_ 132 (2016): 4-12. <https://doi.org/10.1016/j.enbuild.2016.06.094>
[^tab-com]: Loga, Tobias, and Nikolaus Diefenbach. "TABULA Calculation Method-Energy Use for Heating and Domestic Hot Water." _Germany: Institut Wohnen und Umwelt GmbH_ (2013). Available at <https://episcope.eu/building-typology/tabula-structure/calculation/>. Last accessed 01.12.2023.
[^cea-desc]: CEA documentation for intermediate input methods.  Available at <https://github.com/architecture-building-systems/CityEnergyAnalyst/blob/0c483f4553c2d53c866cd8ce4f1ed278cf7ace3b/docs/intermediate_input_methods.rst#L45>
[^BMVBS]: Typologie und Bestand beheizter Nichtwohngebäude in Deutschland Endbericht (Stand:28.07.2011)" vom BMVBS sowie BBSR im BBR
[^EnEV]: Verordnung über energiesparenden Wärmeschutz und energiesparende Anlagentechnik bei Gebäuden (Energieeinsparverordnung - EnEV), 2001.
[^WSchV]: Verordnung über einen energiesparenden Wärmeschutz bei Gebäuden (Wärmeschutzverordnung – WärmeschutzV), 1977.
[^Datenerfassung Umweltschulten]: "Indikatoren zum Wasserverbrauch / Abwasser in Schulen Datenerfassung" from www.umweltschulen.de.
[^BNB]: "Bewertungssystem Nachhaltiges Bauen (BNB) Neubau Büro- und Verwaltungsgebäude" des BMVBS.
[DEHOGA]: "Nachhaltiges Wirtschaften in Hotellerie und Gastronomie -Tipps und Handlungsempfehlungen" des DEHOGA Bundesverbands.
[^IWU-NW-paper]: Hörner, Michael, and Julian Bischof. "Building typology of the non-residential building stock in Germany—Methodology and first results." _ECEEE Summer Study Proceedings; European Council for an Energy Efficient Economy (ECEEE): Hyères, France_ (2022): 935-944. Available at: <https://www.iwu.de/fileadmin/publikationen/gebaeudebestand/2022_ecee_Hoerner-Bischof_Building-typology-of-the-NRBS-in-Germany-Methodology-and-first-Results.pdf>.
[^IWU-NW-data]: Github repository "Nichtwohngebaeude-Typologie-Deutschland" of IWUGERMANY. Available at: <https://github.com/IWUGERMANY/Nichtwohngebaeude-Typologie-Deutschland>.
[^KEA]: KEA-BW (2022): Technikkatalog zur Kommunalen Wärmeplanung.  Available at <https://www.kea-bw.de/fileadmin/user_upload/Waermewende/Wissensportal/Technikkatalog_Tabellen_v1.1.zip>. Last accessed 26.8.23.
[^US]: US INFLATION CALCULATOR. Available at <https://www.usinflationcalculator.com/>. Last accessed 26.8.23.
[^BDEW] : Bundesverbands der Energie- und Wasserwirtschaft
[^Sagner]: Pekka Sagner. "IW-Kurzbericht 11: Wer wohnt wie groß?" Institut der deutschen Wirtschaft. 2021. Köln.
