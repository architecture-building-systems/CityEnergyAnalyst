import pandas as pd

from calendar import isleap


def get_date_range_hours_from_year(year):
    """
    creates date range in hours for the year excluding leap day
    :param year: year of date range
    :type year: int
    :return: pd.date_range with 8760 values
    :rtype: pandas.data_range
    """

    date_range = pd.date_range(start=str(year), end=str(year + 1), freq='H', closed='left')

    # Check if leap year and remove extra day
    if isleap(year):
        date_range = date_range[~((date_range.month == 2) & (date_range.day == 29))]

    return date_range
