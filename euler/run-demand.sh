#!/usr/bin/env sh

# parameters
N=${N:-1}
SCENARIO=${SCENARIO:-$HOME/cea-reference-case/reference-case-open/baseline}
SAMPLES_FOLDER=${SAMPLES_FOLDER:-${SCRATCH}/samples_${METHOD}_${N}}
WEATHER=${WEATHER:-$HOME/CEAforArcGIS/cea/databases/CH/Weather/Zurich.epw}

mkdir -p $SAMPLES_FOLDER

# submit the simulation job
for i in $(seq 0 $END); do echo $i; done
bsub python -m cea.analysis.sensitivity.sensitivity_demand_simulate -i $i -n 12 --scenario $SCENARIO \
     --samples-folder $SAMPLES_FOLDER --simulation-folder \$TMPDIR --weather $WEATHER
