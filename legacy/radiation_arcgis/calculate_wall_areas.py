"""
Calculate the wall area column (Awall_all) in the radiation dataframe and save it back to disk.

This script is run in a separate process to avoid the MemoryError bug.
"""

import os
import pandas as pd


def calculate_wall_areas(radiation):
    """Calculate Awall_all in radiation as the multiplication ``Shape_Leng * FactorShade * Freeheight``
    Uses a subprocess to get around a MemoryError we are having (might have to do with conflicts with ArcGIS numpy?)
    """
    radiation.loc[:, 'Awall_all'] = radiation['Shape_Leng'] * radiation['FactorShade'] * radiation['Freeheight']
    return radiation


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--radiation-pickle', help='path to a pickle of the radiation dataframe')
    args = parser.parse_args()

    radiation = pd.read_pickle(args.radiation_pickle)
    radiation = calculate_wall_areas(radiation)
    radiation.to_pickle(args.radiation_pickle)