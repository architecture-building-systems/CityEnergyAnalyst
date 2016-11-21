#!/usr/bin/env sh
# run just the bsub portion of the demand (for a single batch)

echo "Simulating batch $i with size $NUM_SIMULATIONS"

python -m cea.analysis.sensitivity.sensitivity_demand_simulate -i $i -n $NUM_SIMULATIONS --scenario $SCENARIO \
       --samples-folder $SAMPLES_FOLDER --simulation-folder $TMPDIR --weather $WEATHER
