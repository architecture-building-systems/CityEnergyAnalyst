import pandas as pd

from cea.constants import HOURS_IN_YEAR


def get_dates_from_year(year):
    """
    creates date range for the year of the calculation
    :param year: year of first row in weather file
    :type year: int
    :return: pd.date_range with 8760 values
    :rtype: pandas.data_range
    """
    return pd.date_range(str(year) + '/01/01', periods=HOURS_IN_YEAR, freq='H')