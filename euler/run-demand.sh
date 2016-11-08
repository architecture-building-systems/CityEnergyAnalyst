#!/usr/bin/env sh

# parameters
N=${N:-1}
SCENARIO=${SCENARIO:-$HOME/cea-reference-case/reference-case-open/baseline}
SAMPLES_FOLDER=${SAMPLES_FOLDER:-${SCRATCH}/samples_${METHOD}_${N}}
WEATHER=${WEATHER:-$HOME/CEAforArcGIS/cea/databases/CH/Weather/Zurich.epw}
NUM_SIMULATIONS=${NUM_SIMULATIONS:-100}

mkdir -p $SAMPLES_FOLDER

# submit the simulation jobs (batched to NUM_SIMULATIONS per job)
SAMPLES_COUNT=$(python -m cea.analysis.sensitivity.sensitivity_demand_count -S $SAMPLES_FOLDER)
for ((i=0;i<=SAMPLES_COUNT;i+=NUM_SIMULATIONS)) do
    echo $i
    bsub python -m cea.analysis.sensitivity.sensitivity_demand_simulate -i $i -n $NUM_SIMULATIONS --scenario $SCENARIO \
         --samples-folder $SAMPLES_FOLDER --simulation-folder \$TMPDIR --weather $WEATHER
done
