#!/usr/bin/env sh

# parameters
N=1
SAMPLES_FOLDER=$SCRATCH/samples_morris_$N
SIMULATION_FOLDER=$TMPDIR

mkdir $SAMPLES_FOLDER

# create the samples
python -m cea.analysis.sensitivity.sensitivity_demand_samples --samples-folder $SAMPLES_FOLDER -n $N 
