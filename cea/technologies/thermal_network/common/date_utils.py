"""
Shared date utility for thermal network simulation outputs.
"""

import pandas as pd
from cea.utilities.epwreader import epw_reader
from cea.utilities.date import get_date_range_hours_from_year


def add_date_to_dataframe(locator, df):
    # create date range for the calculation year
    weather_file = locator.get_weather_file()
    weather_data = epw_reader(weather_file)
    year = weather_data['year'][0]
    date_range = get_date_range_hours_from_year(year)

    # Convert date_range to datetime
    date_column = pd.to_datetime(date_range, errors='coerce')

    # Insert the 'date' column at the first position
    df.insert(0, 'date', date_column)

    return df
