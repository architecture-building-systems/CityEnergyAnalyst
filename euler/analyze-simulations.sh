#!/usr/bin/env sh

# parameters
N=${N:-1}
SAMPLES_FOLDER=$SCRATCH/samples_morris_$N
SIMULATION_FOLDER=$TMPDIR

mkdir -p $SAMPLES_FOLDER

# create the samples
python -m cea.analysis.sensitivity.sensitivity_demand_analyze --samples-folder $SAMPLES_FOLDER
