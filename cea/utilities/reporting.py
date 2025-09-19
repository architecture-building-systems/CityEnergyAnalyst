"""
Functions for Report generation
"""
from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import os
from plotly.offline import plot
import plotly.graph_objs as go
from cea.constants import HOURS_IN_YEAR
from dataclasses import fields
from cea.demand.time_series_data import (
    HeatingLoads,
    CoolingLoads,
    ElectricalLoads,
    HeatingSystemTemperatures,
    HeatingSystemMassFlows,
    CoolingSystemTemperatures,
    CoolingSystemMassFlows,
    RCModelTemperatures,
    Moisture,
    VentilationMassFlows,
    EnergyBalanceDashboard,
    Solar,
    Occupancy,
)

if TYPE_CHECKING:
    from cea.demand.time_series_data import TimeSeriesData

__author__ = "Gabriel Happle"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Gabriel Happle", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# TSD keys extracted from dataclass fields - single source of truth
TSD_KEYS_HEATING_LOADS = {field.name for field in fields(HeatingLoads)}
TSD_KEYS_COOLING_LOADS = {field.name for field in fields(CoolingLoads)}
TSD_KEYS_ELECTRICAL_LOADS = {field.name for field in fields(ElectricalLoads)}
TSD_KEYS_ENERGY_BALANCE_DASHBOARD = {field.name for field in fields(EnergyBalanceDashboard)}

# Extract subsets of fields from dataclasses based on naming patterns
TSD_KEYS_HEATING_TEMP = {f.name for f in fields(HeatingSystemTemperatures) if f.name.startswith('ta_')}
TSD_KEYS_HEATING_FLOWS = {f.name for f in fields(HeatingSystemMassFlows) if f.name.startswith('ma_')}
TSD_KEYS_COOLING_TEMP = {f.name for f in fields(CoolingSystemTemperatures) if f.name.startswith('ta_')}
TSD_KEYS_COOLING_FLOWS = {f.name for f in fields(CoolingSystemMassFlows) if f.name.startswith('ma_')}
TSD_KEYS_COOLING_SUPPLY_FLOWS = {f.name for f in fields(CoolingSystemMassFlows) if f.name.startswith('mcp')}
TSD_KEYS_COOLING_SUPPLY_TEMP = {f.name for f in fields(CoolingSystemTemperatures) if f.name.startswith('T')}
TSD_KEYS_HEATING_SUPPLY_FLOWS = {f.name for f in fields(HeatingSystemMassFlows) if f.name.startswith('mcp')}
TSD_KEYS_HEATING_SUPPLY_TEMP = {f.name for f in fields(HeatingSystemTemperatures) if f.name.startswith('T')}
TSD_KEYS_RC_TEMP = {field.name for field in fields(RCModelTemperatures)}
TSD_KEYS_MOISTURE = {field.name for field in fields(Moisture)}
TSD_KEYS_VENTILATION_FLOWS = {field.name for field in fields(VentilationMassFlows)}
TSD_KEYS_SOLAR = {field.name for field in fields(Solar)}
TSD_KEYS_PEOPLE = {field.name for field in fields(Occupancy)}

ALL_KEYS = (TSD_KEYS_PEOPLE | TSD_KEYS_SOLAR | TSD_KEYS_HEATING_LOADS | TSD_KEYS_COOLING_LOADS |
            TSD_KEYS_ELECTRICAL_LOADS | TSD_KEYS_ENERGY_BALANCE_DASHBOARD |
            TSD_KEYS_HEATING_FLOWS | TSD_KEYS_HEATING_SUPPLY_FLOWS | TSD_KEYS_COOLING_FLOWS |
            TSD_KEYS_COOLING_SUPPLY_FLOWS | TSD_KEYS_HEATING_TEMP | TSD_KEYS_HEATING_SUPPLY_TEMP |
            TSD_KEYS_COOLING_TEMP | TSD_KEYS_COOLING_SUPPLY_TEMP | TSD_KEYS_RC_TEMP | TSD_KEYS_MOISTURE |
            TSD_KEYS_VENTILATION_FLOWS)

def calc_full_hourly_dataframe(tsd: TimeSeriesData, date: pd.DatetimeIndex) -> pd.DataFrame:
    """
    This function creates a dataframe with all tsd_df values for full reporting
    """

    tsd_df = pd.DataFrame(index=date, columns=list(ALL_KEYS), dtype=np.float64)
    for key in TSD_KEYS_PEOPLE:
        tsd_df[key] = tsd.get_occupancy_value(key)
    for key in TSD_KEYS_SOLAR:
        tsd_df[key] = tsd.get_solar_value(key)
    for key in TSD_KEYS_HEATING_LOADS | TSD_KEYS_COOLING_LOADS | TSD_KEYS_ELECTRICAL_LOADS | TSD_KEYS_ENERGY_BALANCE_DASHBOARD:
        tsd_df[key] = tsd.get_load_value(key)
    for key in (TSD_KEYS_HEATING_FLOWS | TSD_KEYS_HEATING_SUPPLY_FLOWS | TSD_KEYS_COOLING_FLOWS |
               TSD_KEYS_COOLING_SUPPLY_FLOWS):
        tsd_df[key] = tsd.get_mass_flow_value(key)
    for key in (TSD_KEYS_HEATING_TEMP | TSD_KEYS_HEATING_SUPPLY_TEMP |
               TSD_KEYS_COOLING_TEMP | TSD_KEYS_COOLING_SUPPLY_TEMP | TSD_KEYS_RC_TEMP):
        tsd_df[key] = tsd.get_temperature_value(key)
    for key in TSD_KEYS_MOISTURE:
        tsd_df[key] = tsd.get_moisture_value(key)
    for key in TSD_KEYS_VENTILATION_FLOWS:
        tsd_df[key] = tsd.get_ventilation_mass_flow_value(key)

    return tsd_df

def full_report_to_xls(tsd_df, output_folder, basename):
    """ this function is to write a full report to an ``*.xls`` file containing all intermediate and final results of a
    single building thermal loads calculation"""

    # Create a Pandas Excel writer using XlsxWriter as the engine.
    #timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    #output_path = os.path.join(output_folder,"%(basename)s-%(timestamp)s.xls" % locals())
    output_path = os.path.join(output_folder, f"{basename}.xlsx")
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        tsd_df.to_excel(writer, na_rep="NaN")


def quick_visualization_tsd(tsd_df: pd.DataFrame, output_folder, basename):

    # set to True to produce plotly graphs of selected variables
    plot_heat_load = True
    plot_heat_temp = True
    plot_cool_load = True
    plot_cool_moisture = True
    plot_cool_air = True
    plot_cool_sup = True
    auto_open = False

    heating_plots = {
        'heat-load': (plot_heat_load, TSD_KEYS_HEATING_LOADS),
        'heat-temp': (plot_heat_temp, TSD_KEYS_HEATING_TEMP | TSD_KEYS_RC_TEMP),
    }

    for plot_name, (should_plot, keys) in heating_plots.items():
        if should_plot:
            filename = os.path.join(output_folder, f"{plot_name}-{basename}.html")
            traces = []
            for key in keys:
                x = tsd_df.index[50:150]
                y = tsd_df[key][50:150]
                trace = go.Scattergl(x=x, y=y, name=key, mode='lines+markers')
                traces.append(trace)
            fig = go.Figure(data=traces)
            plot(fig, filename=filename, auto_open=auto_open)

    cooling_plots = {
        'cool-load': (plot_cool_load, TSD_KEYS_COOLING_LOADS),
        'cool-moisture': (plot_cool_moisture, TSD_KEYS_MOISTURE),
        'cool-air': (plot_cool_air, TSD_KEYS_VENTILATION_FLOWS),
        'cool-sup': (plot_cool_sup, TSD_KEYS_COOLING_SUPPLY_TEMP | TSD_KEYS_COOLING_SUPPLY_FLOWS),
    }

    for plot_name, (should_plot, keys) in cooling_plots.items():
        if should_plot:
            filename = os.path.join(output_folder, f"{plot_name}-{basename}.html")
            traces = []

            if len(tsd_df.index) != HOURS_IN_YEAR:
                warnings.warn(f"Warning: The dataframe index length is {len(tsd_df.index)}, expected {HOURS_IN_YEAR}.",
                              UserWarning)

            for key in keys:
                y = tsd_df[key]
                trace = go.Scattergl(x=tsd_df.index, y=y, name=key, mode='lines+markers')
                traces.append(trace)
            fig = go.Figure(data=traces)
            plot(fig, filename=filename, auto_open=auto_open)
