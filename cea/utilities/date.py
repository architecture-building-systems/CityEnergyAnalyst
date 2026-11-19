


import pandas as pd

from calendar import isleap

# Reporting-period labels used by the summary and the KPI cards (meteorological seasons).
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
season_names = ['Spring', 'Summer', 'Autumn', 'Winter']
season_mapping = {
    3: 'Spring', 4: 'Spring', 5: 'Spring',
    6: 'Summer', 7: 'Summer', 8: 'Summer',
    9: 'Autumn', 10: 'Autumn', 11: 'Autumn',
    12: 'Winter', 1: 'Winter', 2: 'Winter'
}


def get_date_range_hours_from_year(year):
    """
    creates date range in hours for the year excluding leap day
    :param year: year of date range
    :type year: int
    :return: pd.date_range with 8760 values
    :rtype: pandas.data_range
    """

    date_range = pd.date_range(start=str(year), end=str(year + 1), freq='h', inclusive='left')

    # Check if leap year and remove extra day
    if isleap(year):
        date_range = date_range[~((date_range.month == 2) & (date_range.day == 29))]

    return date_range


def generate_season_masks(df):
    """
    Generates boolean masks for meteorological seasons based on a DataFrame's DatetimeIndex.

    Meteorological Seasons:
        - Spring: March 1 to May 31
        - Summer: June 1 to August 31
        - Autumn: September 1 to November 30
        - Winter: December 1 to February 28/29

    Parameters:
    ----------
    df : pd.DataFrame or pd.Series
        DataFrame or Series with a DatetimeIndex.

    Returns:
    -------
    dict
        A dictionary containing boolean masks for each season.
        Keys: 'spring', 'summer', 'autumn', 'winter'
    """
    # Ensure the input has a DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("The input must have a Pandas DatetimeIndex.")

    # Extract the month from the index
    month = df.index.month

    # Define masks for each season
    # TODO: enter a function to define the masks based on latitude (northern vs southern hemisphere summers)
    masks = {
        'spring': (month >= 3) & (month <= 5), # march, april, may
        'summer': (month >= 6) & (month <= 8), # june, july, august
        'autumn': (month >= 9) & (month <= 11), # september, october, november
        'winter': (month == 12) | (month <= 2) # december, january, february
    }

    return masks