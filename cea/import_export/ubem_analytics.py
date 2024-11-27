"""
Read CEA results over all scenarios in a project and produce commonly used UBEM metrics.
The list of UBEM metrics include:

- EUI - Grid Electricity [kWh/m²/yr]
  - Annual
- EUI - Enduse Electricity [kWh/m²/yr]
  - Annual
- EUI - Cooling Demand [kWh/m²/yr]
  - Annual
- EUI - Space Cooling Demand [kWh/m²/yr]
  - Annual
- EUI - Heating Demand [kWh/m²/yr]
  - Annual
- EUI - Space Heating Demand [kWh/m²/yr]
  - Annual
- EUI - Domestic Hot Water Demand [kWh/m²/yr]
  - Annual
- PV Energy Penetration [-]
  - Annual
- PV Self-Consumption [-]
  - Annual
- PV Energy Sufficiency [-]
  - Annual
- PV Self-Sufficiency [-]
  - Annual
- PV Capacity Factor [-]
  - Annual
- PV Specific Yield [-]
  - Annual
  - Winter, Spring, Summer, Autumn
  - Winter+Hourly, Spring+Hourly, Summer+Hourly, Autumn+Hourly
  - Daily
  - Weekly
  - Monthly
- PV System Emissions [kgCO₂]
  - Annual
- PV Generation Intensity [kgCO₂/kWh]
  - Annual
  - Winter, Spring, Summer, Autumn
  - Winter+Hourly, Spring+Hourly, Summer+Hourly, Autumn+Hourly
  - Daily
  - Weekly
  - Monthly
- DH Plant Capacity Factor [-]
  - Annual
- DH Pump Capacity Factor [-]
  - Annual
- DC Plant Capacity Factor [-]
  - Annual
- DC Pump Capacity Factor [-]
  - Annual

"""

import os
import numpy as np
import pandas as pd
import cea.config
import time
from cea.utilities.date import get_date_range_hours_from_year
from cea.utilities.date import generate_season_masks
from cea.technologies.solar.photovoltaic import projected_lifetime_output

# warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)


__author__ = "Zhongming Shi, Reynold Mok, Justin McCarty"
__copyright__ = "Copyright 2024, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi, Reynold Mok, Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_capacity_factor(gen_kwh, max_kw):
    """
    caculate the capacity factor of a device

    :param gen_kwh: energy output over a time period
    :type gen_kwh: float or series
    :param max_kw: peak capacity of the system
    :type max_kw: float
    Returns:
    -------
    capacity_factor: float
        the unitless ratio of actual energy output over a year to the theoretical maximum energy output over that period.

    """
    if isinstance(gen_kwh, float):
        len_time_period = 8760
    else:
        len_time_period = len(gen_kwh)
    sum_kWh = gen_kwh.sum()
    capacity_factor = sum_kWh / (max_kw * len_time_period)

    return capacity_factor


def calc_specific_yield(gen_kwh, max_kw, time_period="annual"):
    """
    Calculate the specific yield of the system
    Authors:
    - Justin McCarty

    Parameters:
    ----------
    gen_kwh : pd.Series
        The hourly annual energy generation [kWh] with a DatetimeIndex.
    max_kw: float
        The peak capacity of the system [kWp]
    time_period : str
        The time period over which to calculate self-consumption.
        Options:
            - "annual"
            - "winter", "spring", "summer", "autumn"
            - "1", "2, "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"
    Returns:
    -------
    float
        The calculated specific yield.

    Raises:
    ------
    TypeError:
        - If the input data is not a pandas.Series.
    ValueError:
        - If the `time_period` is invalid.
    """

    # Validate inputs
    if not isinstance(gen_kwh, pd.Series):
        raise TypeError("Both gen_kwh must be Pandas Series.")

    datetime_idx = get_date_range_hours_from_year(2025)

    # Combine the two Series into a DataFrame
    df = pd.DataFrame({"gen_kwh": gen_kwh.values},
                      index=datetime_idx)

    # Calculate self_consumption based on the time_period
    if time_period == "annual":
        annual_gen = df['gen_kwh'].sum()
        specific_yield = annual_gen / max_kw

    elif time_period in ["winter", "spring", "summer", "autumn"]:
        season_mask_dict = generate_season_masks(df)
        if time_period not in season_mask_dict:
            raise ValueError(f"Invalid season specified: {time_period}")

        season_mask = season_mask_dict[time_period]
        season_gen = df.loc[season_mask, 'gen_kwh'].sum()
        specific_yield = season_gen / max_kw

    elif time_period in [str(m) for m in range(1, 13)]:
        month_gen = df.resample("M").sum().iloc[int(time_period) - 1].values[0]
        specific_yield = month_gen / max_kw

    else:
        print(
            f"In calc_specific_yield, the argument 'time_period' was not specified correctly ({time_period}). Using 'annual' by default.")
        annual_gen = df['gen_kwh'].sum()
        specific_yield = annual_gen / max_kw

    return specific_yield


def calc_self_consumption(gen_kwh, demand_kWh, time_period='annual'):
    """
    Calculates self-consumption based on the specified time period.
    Authors:
    - Zhongming Shi
    - Justin McCarty

    Parameters:
    ----------
    gen_kwh : pd.Series
        The hourly annual energy generation [kWh] with a DatetimeIndex.
    demand_kWh : pd.Series
        The hourly annual energy load [kWh] with a DatetimeIndex.
    time_period : str
        The time period over which to calculate self-consumption.
        Options:
            - "annual"
            - "seasonal"
            - "winter", "spring", "summer", "autumn"
            - "winter+hourly", "spring+hourly", "summer+hourly", "autumn+hourly"
            - "daily", "weekly", "monthly"
            - "hourly"

    Returns:
    -------
    float
        The calculated self-consumption ratio.

    Raises:
    ------
    TypeError:
        - If the input data is not a pandas.Series.
    ValueError:
        - If the `time_period` is invalid.
    ZeroDivisionError:
        - If the total generated kWh for a period is zero.
    """

    # Validate inputs
    if not isinstance(gen_kwh, pd.Series) or not isinstance(demand_kWh, pd.Series):
        raise TypeError("Both gen_kwh_df and demand_kWh_df must be Pandas Series.")

    datetime_idx = get_date_range_hours_from_year(2025)

    # Combine the two Series into a DataFrame
    df = pd.DataFrame({"gen_kwh": gen_kwh.values, "demand_kWh": demand_kWh.values},
                      index=datetime_idx)

    # Calculate self_consumption based on the time_period
    if time_period == "annual":
        df_resample = df.resample("A").sum()  # "" stands for year-end frequency
        use = df_resample.min(axis=1)
        total_gen = df['gen_kwh'].sum()
        if total_gen == 0:
            raise ZeroDivisionError("Total generated kWh is zero, cannot divide by zero.")
        self_consumption = use.sum() / total_gen

    elif time_period == "seasonal":
        season_mask_dict = generate_season_masks(df)
        season_results = []
        for season, mask in season_mask_dict.items():
            season_sum = df[mask].sum().rename(season)
            season_results.append(season_sum)
        season_data = pd.concat(season_results, axis=1)
        min_per_season = season_data.min(axis=0)
        total_gen = df['gen_kwh'].sum()
        if total_gen == 0:
            raise ZeroDivisionError("Total generated kWh is zero, cannot divide by zero.")
        self_consumption = min_per_season.sum() / total_gen

    elif time_period in ["winter", "spring", "summer", "autumn", "winter+hourly", "spring+hourly", "summer+hourly",
                         "autumn+hourly"]:
        # Extract the base season
        base_season = time_period.split("+")[0]

        season_mask_dict = generate_season_masks(df)
        if base_season not in season_mask_dict:
            raise ValueError(f"Invalid season specified: {base_season}")
        season_mask = season_mask_dict[base_season]
        season_gen = df.loc[season_mask, 'gen_kwh'].sum()
        season_demand = df.loc[season_mask, 'demand_kWh'].sum()

        if time_period.endswith("+hourly"):
            if base_season not in season_mask_dict:
                raise ValueError(f"Invalid season specified: {base_season}")

            season_mask = season_mask_dict[base_season]
            season_data = df.loc[season_mask]
            use = season_data.min(axis=1).sum()
            total_gen = season_data['gen_kwh'].sum()
            if total_gen == 0:
                raise ZeroDivisionError("Total generated kWh for the season is zero, cannot divide by zero.")
            self_consumption = use / total_gen
        else:
            # Without '+hourly'
            if season_gen == 0:
                raise ZeroDivisionError(f"Total generated kWh for {time_period} is zero, cannot divide by zero.")
            self_consumption = min(season_gen, season_demand) / season_gen

    elif time_period in ["daily", "weekly", "monthly"]:
        freq_codes = {"daily": "D", "weekly": "W", "monthly": "M"}
        resample_code = freq_codes.get(time_period)
        if resample_code is None:
            raise ValueError(f"Invalid time_period: {time_period}. Choose from 'daily', 'weekly', or 'monthly'.")
        df_resample = df.resample(resample_code).sum()
        use = df_resample.min(axis=1)
        total_gen = df['gen_kwh'].sum()
        if total_gen == 0:
            raise ZeroDivisionError("Total generated kWh is zero, cannot divide by zero.")
        self_consumption = use.sum() / total_gen

    elif time_period == "hourly":
        use = df.min(axis=1).sum()
        total_gen = df['gen_kwh'].sum()
        if total_gen == 0:
            raise ZeroDivisionError("Total generated kWh is zero, cannot divide by zero.")
        self_consumption = use / total_gen

    else:
        print(
            f"In calc_self_consumption, the argument 'time_period' was not specified correctly ({time_period}). Using 'hourly' by default.")
        use = df.min(axis=1).sum()
        total_gen = df['gen_kwh'].sum()
        if total_gen == 0:
            raise ZeroDivisionError("Total generated kWh is zero, cannot divide by zero.")
        self_consumption = use / total_gen

    return self_consumption


def calc_self_sufficiency(gen_kwh, demand_kWh, time_period='annual'):
    """
    Calculates self-sufficiency based on the specified time period.
    Authors:
    - Zhongming Shi
    - Justin McCarty

    Parameters:
    ----------
    gen_kwh : pd.Series
        The hourly annual energy generation [kWh] with a DatetimeIndex.
    demand_kWh : pd.Series
        The hourly annual energy load [kWh] with a DatetimeIndex.
    time_period : str
        The time period over which to calculate self-sufficiency.
        Options:
            - "annual"
            - "seasonal"
            - "winter", "spring", "summer", "autumn"
            - "winter+hourly", "spring+hourly", "summer+hourly", "autumn+hourly"
            - "daily", "weekly", "monthly"
            - "hourly"

    Returns:
    -------
    float
        The calculated self-sufficiency ratio.

    Raises:
    ------
    TypeError:
        - If the input data is not a pandas.Series.
    ValueError:
        - If the `time_period` is invalid.
    ZeroDivisionError:
        - If the total generated kWh for a period is zero.
    """

    # Validate inputs
    if not isinstance(gen_kwh, pd.Series) or not isinstance(demand_kWh, pd.Series):
        raise TypeError("Both gen_kwh_df and demand_kWh_df must be Pandas Series.")

    datetime_idx = get_date_range_hours_from_year(2025)

    # Combine the two Series into a DataFrame
    df = pd.DataFrame({"gen_kwh": gen_kwh.values, "demand_kWh": demand_kWh.values},
                      index=datetime_idx)

    # Calculate self_consumption based on the time_period
    if time_period == "annual":
        df_resample = df.resample("A").sum()  # "A" stands for year-end frequency
        use = df_resample.min(axis=1)
        total_demand = df['demand_kWh'].sum()
        if total_demand == 0:
            raise ZeroDivisionError("Total demand kWh is zero, cannot divide by zero.")
        self_sufficiency = use.sum() / total_demand

    elif time_period == "seasonal":
        season_mask_dict = generate_season_masks(df)
        season_results = []
        for season, mask in season_mask_dict.items():
            season_sum = df[mask].sum().rename(season)
            season_results.append(season_sum)
        season_data = pd.concat(season_results, axis=1)
        min_per_season = season_data.min(axis=0)
        total_demand = df['demand_kWh'].sum()
        if total_demand == 0:
            raise ZeroDivisionError("Total demand kWh is zero, cannot divide by zero.")
        self_sufficiency = min_per_season.sum() / total_demand

    elif time_period in ["winter", "spring", "summer", "autumn", "winter+hourly", "spring+hourly", "summer+hourly",
                         "autumn+hourly"]:
        # Extract the base season
        base_season = time_period.split("+")[0]

        season_mask_dict = generate_season_masks(df)
        if base_season not in season_mask_dict:
            raise ValueError(f"Invalid season specified: {base_season}")
        season_mask = season_mask_dict[base_season]
        season_gen = df.loc[season_mask, 'gen_kwh'].sum()
        season_demand = df.loc[season_mask, 'demand_kWh'].sum()

        if time_period.endswith("+hourly"):
            if base_season not in season_mask_dict:
                raise ValueError(f"Invalid season specified: {base_season}")

            season_mask = season_mask_dict[base_season]
            season_data = df.loc[season_mask]
            use = season_data.min(axis=1).sum()
            total_demand = season_data['demand_kWh'].sum()
            if total_demand == 0:
                raise ZeroDivisionError("Total demand kWh for the season is zero, cannot divide by zero.")
            self_sufficiency = use / total_demand
        else:
            # Without '+hourly'
            if season_demand == 0:
                raise ZeroDivisionError(f"Total demand kWh for {time_period} is zero, cannot divide by zero.")
            self_sufficiency = min(season_gen, season_demand) / season_demand

    elif time_period in ["daily", "weekly", "monthly"]:
        freq_codes = {"daily": "D", "weekly": "W", "monthly": "M"}
        resample_code = freq_codes.get(time_period)
        if resample_code is None:
            raise ValueError(f"Invalid time_period: {time_period}. Choose from 'daily', 'weekly', or 'monthly'.")
        df_resample = df.resample(resample_code).sum()
        use = df_resample.min(axis=1)
        total_demand = df['demand_kWh'].sum()
        if total_demand == 0:
            raise ZeroDivisionError("Total demand kWh is zero, cannot divide by zero.")
        self_sufficiency = use.sum() / total_demand

    elif time_period == "hourly":
        use = df.min(axis=1).sum()
        total_demand = df['demand_kWh'].sum()
        if total_demand == 0:
            raise ZeroDivisionError("Total demand kWh is zero, cannot divide by zero.")
        self_sufficiency = use.sum() / total_demand

    else:
        print(f"The argument 'time_period' was not specified correctly ({time_period}). Using 'hourly' by default.")
        use = df.min(axis=1).sum()
        total_demand = df['demand_kWh'].sum()
        if total_demand == 0:
            raise ZeroDivisionError("Total demand kWh is zero, cannot divide by zero.")
        self_sufficiency = use.sum() / total_demand

    return self_sufficiency


def calc_generation_intensity(generator_embodied_emissions_kgco2, lifetime_electricity_generated_kwh,
                              time_period="annual"):
    """
    Calculates self-sufficiency based on the specified time period.
    Authors:
    - Justin McCarty

    Parameters:
    ----------
    generator_embodied_emissions_kgco2 : float
        the emboided emissions assocated to the generation device in kgCO2e
    lifetime_electricity_generated_kwh : pd.Series
        The sum of lifetime generation for each hour of the year in kWh
    time_period : str
        The time period over which to calculate self-sufficiency.
        Options:
            - "annual"
            - "winter", "spring", "summer", "autumn"
            - "1", "2, "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"

    Returns:
    -------
    float
        The calculated generation intensity of the generation device in kgCO2e/kWh.

    Raises:
    ------
    TypeError:
        - If the input data is not a pandas.Series.
    ValueError:
        - If the `time_period` is invalid.
    ZeroDivisionError:
        - If the total generated kWh for a period is zero.
    """

    # Validate inputs
    if not isinstance(lifetime_electricity_generated_kwh, np.ndarray):
        raise TypeError("Both gen_kwh must be numpy array.")

    datetime_idx = get_date_range_hours_from_year(2025)

    # Combine the two Series into a DataFrame
    df = pd.DataFrame({"gen_kwh": lifetime_electricity_generated_kwh},
                      index=datetime_idx)

    # Calculate self_consumption based on the time_period
    if time_period == "annual":
        annual_gen = df['gen_kwh'].sum()
        module_generation_intensity_kgco2kwh = generator_embodied_emissions_kgco2 / annual_gen

    elif time_period in ["winter", "spring", "summer", "autumn"]:
        season_mask_dict = generate_season_masks(df)
        if time_period not in season_mask_dict:
            raise ValueError(f"Invalid season specified: {time_period}")

        season_mask = season_mask_dict[time_period]
        season_gen = df.loc[season_mask, 'gen_kwh'].sum()
        module_generation_intensity_kgco2kwh = generator_embodied_emissions_kgco2 / season_gen

    elif time_period in [str(m) for m in range(1, 13)]:
        month_gen = df.resample("M").sum().iloc[int(time_period) - 1].values[0]
        module_generation_intensity_kgco2kwh = generator_embodied_emissions_kgco2 / month_gen

    else:
        print(
            f"In calc_generation_intensity, the argument 'time_period' was not specified correctly ({time_period}). Using 'annual' by default.")
        annual_gen = df['gen_kwh'].sum()
        module_generation_intensity_kgco2kwh = generator_embodied_emissions_kgco2 / annual_gen

    return module_generation_intensity_kgco2kwh


def calc_simple_pv_payback(annual_generation_kwh, annual_electricity_demand_kwh, system_capital_cost,
                           system_operating_rate, lifetime, interest_rate, electricity_purchase_cost,
                           electricity_sell_value):
    return lifetime


def exec_read_and_analyse(cea_scenario):
    """
    read the CEA results and calculates the UBEM metrics listed at the top of this script

    :param cea_scenario: path to the CEA scenario to be assessed using CEA
    :type cea_scenario: file path
    Returns:
    -------
    analytics_df: pd.DataFrame
        A dataframe of the metrics at the top of this script.

    """
    # create an empty DataFrame to store all the results
    analytics_results_dict = dict()

    # intialise the controls and start adding default controls assuming everything can be run
    control_dict = {
    "old_generator_database": False,
    "skip_demand": False,
    "skip_dh": False,
    "skip_dc": False
    }

    # intialize the time periods
    # Todo this should be a config option?
    time_period_options_autarky = [
        "annual",
        "seasonal",
        "winter",
        "spring",
        "summer",
        "autumn",
        "winter+hourly",
        "spring+hourly",
        "summer+hourly",
        "autumn+hourly",
        "daily",
        "weekly",
        "monthly",
        "hourly"
    ]

    time_period_options_yield = [
        "annual",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "11",
        "12",
        "winter",
        "spring",
        "summer",
        "autumn"
    ]
    month_string_number = [str(m) for m in range(1,13)]
    month_string = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    time_period_dict = dict(zip(month_string_number,month_string))

    time_period_options_generation_intensity = time_period_options_yield

    # start by checking for files
    # set up the paths
    total_demand_buildings_path = os.path.join(cea_scenario, 'outputs/data/demand/Total_demand.csv')
    pv_database_path = os.path.join(cea_scenario, 'inputs/technology/components/CONVERSION.xlsx')

    # grab panel types for PV
    pv_database_df = pd.read_excel(pv_database_path, sheet_name="PHOTOVOLTAIC_PANELS")
    panel_types = list(set(pv_database_df['code']))
    new_database_columns = ["capacity_Wp",
                            "module_area_m2",
                            "primary_energy_kWh_m2",
                            "cost_facade_euro_m2",
                            "cost_roof_euro_m2",
                            "module_embodied_kgco2m2"]
    for col in new_database_columns:
        if col not in pv_database_df.columns:
            control_dict["old_generator_database"] = True

    # hourly demand data for each building
    cea_result_demand_hourly_df = pd.DataFrame()

    # power plants
    dh_plant_thermal_path = os.path.join(cea_scenario, 'outputs/data/thermal-networkDH__plant_thermal_load_kW.csv')
    dh_plant_pumping_path = os.path.join(cea_scenario, 'outputs/data/thermal-networkDH__plant_pumping_load_kW.csv')
    dc_plant_thermal_path = os.path.join(cea_scenario, 'outputs/data/thermal-network/DC__plant_thermal_load_kW.csv')
    dc_plant_pumping_path = os.path.join(cea_scenario, 'outputs/data/thermal-network/DC__plant_pumping_load_kW.csv')

    try:
        cea_result_total_demand_buildings_df = pd.read_csv(total_demand_buildings_path)
    except FileNotFoundError:
        print(
            f"File {total_demand_buildings_path} not found. All building demand results currently required for analysis. Returning empty dataframe")
        cea_result_total_demand_buildings_df = pd.DataFrame
        return cea_result_total_demand_buildings_df

    demand_dir = os.path.join(cea_scenario, 'outputs/data/demand')
    demand_by_building = os.listdir(demand_dir)

    for file in demand_by_building:
        try:
            if file.endswith('.csv') and not file.startswith('Total_demand.csv'):
                demand_building_path = os.path.join(demand_dir, file)
                cea_result_demand_building_df = pd.DataFrame()
                cea_result_demand_building_df['GRID_kWh'] = pd.read_csv(demand_building_path)['GRID_kWh']
                cea_result_demand_hourly_df = pd.concat([cea_result_demand_building_df, cea_result_demand_hourly_df],
                                                        axis=1).reindex(cea_result_demand_building_df.index)
            else:
                pass
            cea_result_demand_hourly_df.loc[:, 'district_GRID_kWh'] = cea_result_demand_hourly_df.sum(axis=1)
        except FileNotFoundError:
            control_dict["skip_demand"] = True
            print(
                f"File {file} not found. All building demand results currently required for analysis. Returning empty dataframe")
            return cea_result_demand_hourly_df

    # not found message to be reflected in the analytics DataFrame
    na = float('Nan')
    missing_panel_list = []
    for panel_type in panel_types:
        control_dict[panel_type] = {}
        pv_buildings_path = os.path.join(cea_scenario,
                                         f'outputs/data/potentials/solar/PV_{panel_type}_total_buildings.csv')
        pv_hourly_path = os.path.join(cea_scenario,
                                      f'outputs/data/potentials/solar/PV_{panel_type}_total.csv')
        try:
            pd.read_csv(pv_buildings_path)
            pd.read_csv(pv_hourly_path)
            control_dict[panel_type]['skip_capacity_factor'] = False
            control_dict[panel_type]['skip_specific_yield'] = False
            control_dict[panel_type]['skip_generation_intensity'] = False
            control_dict[panel_type]['skip_autarky'] = False


        except FileNotFoundError:
            missing_panel_list.append(panel_type)
            analytics_results_dict[f'PV_{panel_type}_energy_penetration[-]'] = na

            control_dict[panel_type]['skip_capacity_factor'] = True
            analytics_results_dict[f'PV_{panel_type}_capacity_factor[-]'] = na

            control_dict[panel_type]['skip_specific_yield'] = True
            for time_period in time_period_options_yield:
                if time_period in month_string_number:
                    analytics_results_dict[f'PV_{panel_type}_specific_yield_{time_period_dict[time_period]}[kwh/kwp]'] = na
                else:
                    analytics_results_dict[f'PV_{panel_type}_specific_yield_{time_period}[kwh/kwp]'] = na

            control_dict[panel_type]['skip_generation_intensity'] = True
            for time_period in time_period_options_generation_intensity:
                if time_period in month_string_number:
                    analytics_results_dict[
                        f'PV_{panel_type}_generation_intensity_{time_period_dict[time_period]}[kgco2kwh]'] = na
                else:
                    analytics_results_dict[
                    f'PV_{panel_type}_generation_intensity_{time_period}[kgco2kwh]'] = na

            control_dict[panel_type]['skip_autarky'] = True
            for time_period in time_period_options_autarky:
                analytics_results_dict[f'PV_{panel_type}_self_consumption_{time_period}[-]'] = na
                analytics_results_dict[f'PV_{panel_type}_self_sufficiency_{time_period}[-]'] = na

        # return analytics_results_dict

    # try for demand related metrics
    try:
        cea_result_total_demand_buildings_df = pd.read_csv(total_demand_buildings_path)

    except FileNotFoundError:
        print(f"{total_demand_buildings_path} missing.")
        control_dict["skip_demand"] = True

        analytics_results_dict['EUI - grid electricity [kWh/m2/yr]'] = na
        analytics_results_dict['EUI - enduse electricity [kWh/m2/yr]'] = na
        analytics_results_dict['EUI - cooling demand [kWh/m2/yr]'] = na
        analytics_results_dict['EUI - space cooling demand [kWh/m2/yr]'] = na
        analytics_results_dict['EUI - heating demand [kWh/m2/yr]'] = na
        analytics_results_dict['EUI - space heating demand [kWh/m2/yr]'] = na
        analytics_results_dict['EUI - domestic hot water demand [kWh/m2/yr]'] = na

    # try for thermal power plants
    try:
        pd.read_csv(dh_plant_thermal_path)
        pd.read_csv(dh_plant_pumping_path)

    except FileNotFoundError:
        # thermal plants
        control_dict['skip_dh'] = True
        analytics_results_dict['DH_plant_capacity_factor[-]'] = na
        analytics_results_dict['DH_pump_capacity_factor[-]'] = na

    try:
        pd.read_csv(dc_plant_thermal_path)
        pd.read_csv(dc_plant_pumping_path)

    except FileNotFoundError:
        # thermal plants
        control_dict['skip_dc'] = True
        analytics_results_dict['DC_plant_capacity_factor[-]'] = na
        analytics_results_dict['DC_pump_capacity_factor[-]'] = na

    if not control_dict['skip_demand']:

        analytics_results_dict['EUI - grid electricity [kWh/m2/yr]'] = cea_result_total_demand_buildings_df[
                                                                           'GRID_MWhyr'].sum() / \
                                                                       cea_result_total_demand_buildings_df[
                                                                           'GFA_m2'].sum() * 1000
        analytics_results_dict['EUI - enduse electricity [kWh/m2/yr]'] = cea_result_total_demand_buildings_df[
                                                                             'E_sys_MWhyr'].sum().sum() / \
                                                                         cea_result_total_demand_buildings_df[
                                                                             'GFA_m2'].sum() * 1000
        analytics_results_dict['EUI - cooling demand [kWh/m2/yr]'] = cea_result_total_demand_buildings_df[
                                                                         'QC_sys_MWhyr'].sum() / \
                                                                     cea_result_total_demand_buildings_df[
                                                                         'GFA_m2'].sum() * 1000
        analytics_results_dict['EUI - space cooling demand [kWh/m2/yr]'] = cea_result_total_demand_buildings_df[
                                                                               'Qcs_sys_MWhyr'].sum() / \
                                                                           cea_result_total_demand_buildings_df[
                                                                               'GFA_m2'].sum() * 1000
        analytics_results_dict['EUI - heating demand [kWh/m2/yr]'] = cea_result_total_demand_buildings_df[
                                                                         'QH_sys_MWhyr'].sum() / \
                                                                     cea_result_total_demand_buildings_df[
                                                                         'GFA_m2'].sum() * 1000
        analytics_results_dict['EUI - space heating demand [kWh/m2/yr]'] = cea_result_total_demand_buildings_df[
                                                                               'Qhs_MWhyr'].sum() / \
                                                                           cea_result_total_demand_buildings_df[
                                                                               'GFA_m2'].sum() * 1000
        analytics_results_dict['EUI - domestic hot water demand [kWh/m2/yr]'] = cea_result_total_demand_buildings_df[
                                                                                    'Qww_MWhyr'].sum() / \
                                                                                cea_result_total_demand_buildings_df[
                                                                                    'GFA_m2'].sum() * 1000

    # metrics for on-site solar energy use
    for panel_type in panel_types:
        if panel_type in missing_panel_list:
            continue

        module = pv_database_df[pv_database_df["code"] == panel_type].iloc[0]
        pv_buildings_path = os.path.join(cea_scenario,
                                         f'outputs/data/potentials/solar/PV_{panel_type}_total_buildings.csv')
        cea_result_pv_buildings_df = pd.read_csv(pv_buildings_path)
        pv_hourly_path = os.path.join(cea_scenario,
                                      f'outputs/data/potentials/solar/PV_{panel_type}_total.csv')
        cea_result_pv_hourly_df = pd.read_csv(pv_hourly_path)

        # energy penetration
        analytics_results_dict[f'PV_{panel_type}_energy_penetration[-]'] = cea_result_pv_buildings_df[
                                                                               'E_PV_gen_kWh'].sum() / (
                                                                                   cea_result_total_demand_buildings_df[
                                                                                       'GRID_MWhyr'].sum() * 1000)

        if not control_dict['old_generator_database']:
            module_capacity_kWp = module["capacity_Wp"] / 1000
            module_area_m2 = module["module_area_m2"]
            module_impact_kgco2m2 = module["module_embodied_kgco2m2"]
            system_area_m2 = cea_result_pv_buildings_df['Area_PV_m2'].sum()
            system_impact_kgco2 = module_impact_kgco2m2 * system_area_m2
            n_modules = system_area_m2 / module_area_m2
            max_kw = module_capacity_kWp * n_modules

            # capacity factor
            if not control_dict[panel_type]['skip_capacity_factor']:
                analytics_results_dict[f'PV_{panel_type}_capacity_factor[-]'] = calc_capacity_factor(
                    cea_result_pv_buildings_df['E_PV_gen_kWh'],
                    max_kw)

            # autarky
            if not control_dict[panel_type]['skip_autarky']:
                for time_period in time_period_options_autarky:
                    analytics_results_dict[
                        f'PV_{panel_type}_self_consumption_{time_period}[-]'] = calc_self_consumption(
                        cea_result_pv_hourly_df['E_PV_gen_kWh'],
                        cea_result_demand_hourly_df['district_GRID_kWh'],
                        time_period=time_period)
                    analytics_results_dict[
                        f'PV_{panel_type}_self_sufficiency_{time_period}[-]'] = calc_self_sufficiency(
                        cea_result_pv_hourly_df['E_PV_gen_kWh'],
                        cea_result_demand_hourly_df['district_GRID_kWh'],
                        time_period=time_period)

            if not control_dict[panel_type]['skip_specific_yield']:
                # specific yield
                for time_period in time_period_options_yield:
                    if time_period in month_string_number:

                        analytics_results_dict[f'PV_{panel_type}_specific_yield_{time_period_dict[time_period]}[kwh/kwp]'] = calc_specific_yield(
                            cea_result_pv_hourly_df['E_PV_gen_kWh'],
                            max_kw,
                            time_period=time_period)
                    else:

                        analytics_results_dict[f'PV_{panel_type}_specific_yield_{time_period}[kwh/kwp]'] = calc_specific_yield(
                            cea_result_pv_hourly_df['E_PV_gen_kWh'],
                            max_kw,
                            time_period=time_period)


            if not control_dict[panel_type]['skip_generation_intensity']:
                module_lifetime_years = int(module["LT_yr"])
                lifetime_generation_kWh = projected_lifetime_output(cea_result_pv_hourly_df['E_PV_gen_kWh'].values,
                                                                    module_lifetime_years)
                # generation intensity
                for time_period in time_period_options_generation_intensity:
                    if time_period in month_string_number:
                        analytics_results_dict[
                        f'PV_{panel_type}_generation_intensity_{time_period_dict[time_period]}[kgco2kwh]'] = calc_generation_intensity(system_impact_kgco2,
                                                                                     lifetime_generation_kWh.sum(
                                                                                         axis=0),
                                                                                     time_period=time_period)
                    else:
                        analytics_results_dict[
                        f'PV_{panel_type}_generation_intensity_{time_period}[kgco2kwh]'] = calc_generation_intensity(system_impact_kgco2,
                                                                                     lifetime_generation_kWh.sum(
                                                                                         axis=0),
                                                                                     time_period=time_period)

        else:
            analytics_results_dict[f'PV_{panel_type}_capacity_factor[-]'] = na
            for time_period in time_period_options_yield:
                analytics_results_dict[f'PV_{panel_type}_specific_yield_{time_period}[kwh/kwp]'] = na
            for time_period in time_period_options_generation_intensity:
                analytics_results_dict[
                    f'PV_{panel_type}_generation_intensity_{time_period}[kgco2kwh]'] = na
            for time_period in time_period_options_autarky:
                analytics_results_dict[f'PV_{panel_type}_self_consumption_{time_period}[-]'] = na
                analytics_results_dict[f'PV_{panel_type}_self_sufficiency_{time_period}[-]'] = na

    # thermal power plants
    if not control_dict['skip_dh']:
        cea_result_dh_thermal_df = pd.read_csv(dh_plant_thermal_path)
        cea_result_dh_pumping_df = pd.read_csv(dh_plant_pumping_path)
        analytics_results_dict['DH_plant_capacity_factor[-]'] = calc_capacity_factor(
            cea_result_dh_thermal_df['thermal_load_kW'],
            cea_result_dh_thermal_df[
                'thermal_load_kW'].max())
        analytics_results_dict['DH_pump_capacity_factor[-]'] = calc_capacity_factor(
            cea_result_dh_pumping_df['pressure_loss_total_kW'],
            cea_result_dh_pumping_df['pressure_loss_total_kW'].max())
    if not control_dict['skip_dc']:
        cea_result_dc_thermal_df = pd.read_csv(dc_plant_thermal_path)
        cea_result_dc_pumping_df = pd.read_csv(dc_plant_pumping_path)
        analytics_results_dict['DC_plant_capacity_factor[-]'] = calc_capacity_factor(
            cea_result_dc_thermal_df['thermal_load_kW'],
            cea_result_dc_thermal_df[
                'thermal_load_kW'].max())
        analytics_results_dict['DC_pump_capacity_factor[-]'] = calc_capacity_factor(
            cea_result_dc_pumping_df['pressure_loss_total_kW'],
            cea_result_dc_pumping_df['pressure_loss_total_kW'].max())

    analytics_df = pd.DataFrame([analytics_results_dict])
    analytics_df = analytics_df.reindex(sorted(analytics_df.columns), axis=1)
    return analytics_df


def main(config):
    """
    Read through CEA results for all scenarios under a project and generate UBEM metrics for quick analytics.

    :param config: the configuration object to use
    :type config: cea.config.Configuration
    :return:
    """

    # Start the timer
    t0 = time.perf_counter()

    assert os.path.exists(config.general.project), 'input file not found: %s' % config.project

    project_path = config.general.project
    scenario_name = config.general.scenario_name
    project_boolean = config.result_analytics.all_scenarios

    # deciding to run all scenarios or the current the scenario only
    if project_boolean:
        scenarios_list = os.listdir(project_path)
    else:
        scenarios_list = [scenario_name]

    # loop over one or all scenarios under the project
    analytics_project_df = pd.DataFrame()
    for scenario in scenarios_list:
        # Ignore hidden directories
        if scenario.startswith('.') or os.path.isfile(os.path.join(project_path, scenario)):
            continue

        cea_scenario = os.path.join(project_path, scenario)
        print(f'Reading and analysing the CEA results for Scenario {cea_scenario}.')
        # executing CEA commands
        analytics_scenario_df = exec_read_and_analyse(cea_scenario)
        # analytics_scenario_df['scenario_name'] = scenario
        analytics_project_df = pd.concat([analytics_project_df, analytics_scenario_df])

    #todo contemplate if we should change the orientaiton of the table to have a column as scenario and rows as metrics

    # write the results
    if project_boolean:
        analytics_project_path = os.path.join(config.general.project, 'result_analytics.csv')
        analytics_project_df.to_csv(analytics_project_path, index=False, float_format='%.2f')

    else:
        analytics_scenario_path = os.path.join(project_path, scenario_name,
                                               f'{scenario_name}_result_analytics.csv')
        analytics_project_df.to_csv(analytics_scenario_path, index=False, float_format='%.2f')

    # Print the time used for the entire processing
    time_elapsed = time.perf_counter() - t0
    print('The entire process of read-and-analyse is now completed - time elapsed: %d.2 seconds' % time_elapsed)


if __name__ == '__main__':
    main(cea.config.Configuration())
