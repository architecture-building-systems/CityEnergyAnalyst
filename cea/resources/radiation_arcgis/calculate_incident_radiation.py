import numpy as np
import pandas as pd


def calculate_incident_radiation(radiation, radiation_csv):
    """
    Calculate the output file "radiation_csv" based on the radiation dataframe.
    :param radiation:
    :param radiation_csv:
    :return:
    """

    # Import Radiation table and compute the Irradiation in W in every building's surface
    hours_in_year = 8760
    column_names = ['T%i' % (i + 1) for i in range(hours_in_year)]
    for column in column_names:
        # transform all the points of solar radiation into Wh
        radiation[column] = radiation[column] * radiation['Awall_all']

    # sum up radiation load per building
    # NOTE: this looks like an ugly hack because it is: in order to work around a pandas MemoryError, we group/sum the
    # columns individually...
    grouped_data_frames = {}
    for column in column_names:
        df = pd.DataFrame(data={'Name': radiation['Name'],
                                column: radiation[column]})
        grouped_data_frames[column] = df.groupby(by='Name').sum()
    radiation_load = pd.DataFrame(index=grouped_data_frames.values()[0].index)
    for column in column_names:
        radiation_load[column] = grouped_data_frames[column][column]

    incident_radiation = np.round(radiation_load[column_names], 2)
    incident_radiation.to_csv(radiation_csv)

    return  # total solar radiation in areas exposed to radiation in Watts


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--radiation-pickle', help='path to a pickle of the radiation dataframe')
    parser.add_argument('--radiation-csv', help='path to a pickle of the radiation dataframe')
    args = parser.parse_args()

    radiation = pd.read_pickle(args.radiation_pickle)
    calculate_incident_radiation(radiation, args.radiation_csv)
