#!/usr/bin/env sh
# run just the bsub portion of the demand (for a single batch)
# The reason that the call to `sensitivity_demand_simulate` was extracted to it's own script is because the
# variable `$TMPDIR` is not set at the time `bsub` is called, only when the job is actually running on a node.
# (it might be possible to escape the variable somehow, I just haven't figured out how...)

# ---
# author: Daren Thomas
# copyright: Copyright 2016, Architecture and Building Systems - ETH Zurich
# credits: Daren Thomas
# license: MIT
# version:  0.1
# maintainer: Daren Thomas
# email: cea@arch.ethz.ch
# status: Production
# ---

echo "Simulating batch $i with size $NUM_SIMULATIONS"

python -m cea.analysis.sensitivity.sensitivity_demand_simulate -i $i -n $NUM_SIMULATIONS --scenario $SCENARIO \
       --samples-folder $SAMPLES_FOLDER --simulation-folder $TMPDIR --weather $WEATHER
