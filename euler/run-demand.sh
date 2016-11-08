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

echo "Submitting LSF jobs for $SAMPLES_COUNT simulations"

for ((i=0;i<=SAMPLES_COUNT;i+=NUM_SIMULATIONS)) do
    export i
    export NUM_SIMULATIONS
    export N
    export SCENARIO
    export SAMPLES_FOLDER
    export WEATHER
    echo "Submitting batch starting at sample $i with size $NUM_SIMULATIONS"
    bsub sh $HOME/CEAforArcGIS/euler/run-demand-bsub.sh
done
