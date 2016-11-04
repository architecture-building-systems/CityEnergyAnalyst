#!/usr/bin/env sh

# parameters
N=1
SCENARIO=$HOME/cea-reference-case/reference-case-open/baseline
SAMPLES_FOLDER=$SCRATCH/samples_morris_$N
WEATHER=$HOME/CEAforArcGIS/cea/databases/CH/Weather/Zurich.epw

mkdir -p $SAMPLES_FOLDER

# submit the simulation job
bsub python -m cea.analysis.sensitivity.sensitivity_demand_simulate -i 0 -n 12 --scenario $SCENARIO \
     --samples-folder $SAMPLES_FOLDER --simulation-folder \$TMPDIR --weather $WEATHER
