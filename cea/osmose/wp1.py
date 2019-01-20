from __future__ import division
import numpy as np
import pandas as pd
import os

import cea.osmose.extract_demand_outputs as extract_demand_outputs
import cea.osmose.run_osmose as run_osmose
import cea.osmose.plot_osmose_result as plot_results

TECHS = ['HCS_coil', 'HCS_ER0', 'HCS_3for2', 'HCS_LD', 'HCS_IEHX']
# TECHS = ['HCS_coil']

def main():
    # extract demand outputs
    case = 'WTP_CBD_m_WP1_HOT'
    start_t = 5040  # 5/16: 3240, Average Annual 7/30-8/5: 5040-5207
    timesteps = 168  # 168 (week)
    _ = extract_demand_outputs.extract_cea_outputs_to_osmose_main(case, start_t, timesteps)
    building_names = ['B001'] # FIXME: temporary

    # run osmose
    for building in building_names:
        pause(building)
        for tech in TECHS:
            run_osmose.exec_osmose(tech)
        # plot_results.main(building, TECHS) #TODO: change paths in osmose

    return np.nan


def pause(building):
    print "Change building name in frontend to ", building
    return raw_input("press ENTER to continue")


if __name__ == '__main__':
    main()