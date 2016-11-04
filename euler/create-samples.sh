#!/usr/bin/env sh

# parameters
N=1
SAMPLES_FOLDER=/cluster/scratch/username/samples
SIMULATION_FOLDER=$TMPDIR


# create the samples
python -m cea.analysis.sensitivity.sensitivity_demand_samples.py --samples-folder $SAMPLES_FOLDER -n $N \
   --simulation-folder $SIMULATION_FOLDER

