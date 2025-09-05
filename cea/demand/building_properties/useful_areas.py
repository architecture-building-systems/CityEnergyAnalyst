from __future__ import annotations

from typing import TYPE_CHECKING

from cea.demand.constants import LAMBDA_AT

if TYPE_CHECKING:
    import pandas as pd

# TODO: Double check usages of this function
def calc_useful_areas(df: pd.DataFrame) -> pd.DataFrame:
    # Calculate share of above- and below-ground GFA that is conditioned/occupied (assume same share on all floors)
    df['Hs_ag'], df['Hs_bg'], df['Ns_ag'], df['Ns_bg'] = split_above_and_below_ground_shares(
        df['Hs'], df['Ns'], df['occupied_bg'], df['floors_ag'] - df['void_deck'], df['floors_bg'])
    # occupied floor area: all occupied areas in the building
    df['Aocc'] = df['GFA_ag_m2'] * df['Ns_ag'] + df['GFA_bg_m2'] * df['Ns_bg']
    # conditioned area: areas that are heated/cooled
    df['Af'] = df['GFA_ag_m2'] * df['Hs_ag'] + df['GFA_bg_m2'] * df['Hs_bg']
    # electrified area: share of gross floor area that is also electrified
    df['Aef'] = df['GFA_m2'] * df['Es']
    # area of all surfaces facing the building zone
    df['Atot'] = df['Af'] * LAMBDA_AT

    return df


def split_above_and_below_ground_shares(Hs, Ns, occupied_bg, floors_ag, floors_bg):
    """
    Split conditioned (Hs) and occupied (Ns) shares of ground floor area based on whether the basement
    conditioned/occupied or not.
    For simplicity, the same share is assumed for all conditioned/occupied floors (whether above or below ground)
    """
    share_ag = floors_ag / (floors_ag + floors_bg * occupied_bg)
    share_bg = 1 - share_ag
    Hs_ag = Hs * share_ag
    Hs_bg = Hs * share_bg
    Ns_ag = Ns * share_ag
    Ns_bg = Ns * share_bg

    return Hs_ag, Hs_bg, Ns_ag, Ns_bg
