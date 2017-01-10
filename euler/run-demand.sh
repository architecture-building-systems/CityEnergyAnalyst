#!/usr/bin/env sh

# Submits the simulation jobs (calls to `cea/analysis/sensitivity/sensitivity_demand_simulate.py`) to the Euler job
# scheduler using the `bjobs` program. The simulation jobs are batched by the $NUM_SIMULATIONS variable in order
# to minimize the overhead of spinning up many jobs: Each job will simulate $NUM_SIMULATION jobs.
#
# In order to be able to use the `$TMPDIR` variable as the simulation folder, the job passed to `bjobs` is not the
# `sensitivity_demand_simulate.py` call, but instead `run-demand-bsub.sh`, which calls `sensitivity_demand_simulate.py`.
#
# See the documentation of `sensitivity_demand_simulate.py` for more information on the simulation script.
# Provides a handy interface using environment variables and default values tailored to the Euler cluster.
#
# Each parameter is set to the environment variable of the same name or the default value if not set.
# The samples folder is created if it doesn't yet exist.
# The --simulation-folder is set to $TMPDIR for the Euler scripts.

# This is the mapping of environment variables to argument names of the `sensitivity_demand_simulate.py` script:
#
# environment variable | corresponding argument
# N                    | (not used, except for calculating the default $SAMPLES_FOLDER value)
# METHOD               | --method
# SCENARIO             | --scenario
# SAMPLES_FOLDER       | --samples-folder
# WEATHER              | --weather
# NUM_SIMULATIONS      | --number-of-simulations
# OUTPUT_PARAMETERS    | FIXME: not implemented yet! --output-parameters
# VARIABLE_GROUPS      | FIXME: not implemented yet! --variable-groups

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

# parameters (the syntax used can be learnt here: http://stackoverflow.com/a/2013589/2260
# and here: http://wiki.bash-hackers.org/syntax/pe)
N=${N:-1}
METHOD=${METHOD:-sobol}
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
    export PYTHONUNBUFFERED=1
    echo "Submitting batch starting at sample $i with size $NUM_SIMULATIONS"
    bsub sh $HOME/CEAforArcGIS/euler/run-demand-bsub.sh
done
