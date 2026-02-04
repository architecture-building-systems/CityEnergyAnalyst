#!/usr/bin/env sh

# Runs the script `cea/analysis/sensitivity/sensitivity_demand_samples.py` to set up the samples folder and problem
# statement for the sensitivity analysis.
# Provides a handy interface using environment variables and default values tailored to the Euler cluster.

# Each parameter is set to the environment variable of the same name or the default value if not set.
# The samples folder is created if it doesn't yet exist.
# This is the mapping of environment variables to argument names of the `sensitivity_demand_samples.py` script:
#
# environment variable | corresponding argument
# N                    | --num-samples (-n)
# METHOD               | --method
# SAMPLES_FOLDER       | --samples-folder
# CALC_SECOND_ORDER    | --calc-second-order
# NUM_LEVELS           | --num-levels
# VARIABLE_GROUPS      | --variable-groups

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
SAMPLES_FOLDER=${SAMPLES_FOLDER:-${SCRATCH}/samples_${METHOD}_${N}}
CALC_SECOND_ORDER=${CALC_SECOND_ORDER:-0}
NUM_LEVELS=${NUM_LEVELS:-4}
VARIABLE_GROUPS=${VARIABLE_GROUPS:-ENVELOPE INDOOR_COMFORT INTERNAL_LOADS}

mkdir -p $SAMPLES_FOLDER

# create the samples
echo "Creating samples $METHOD $N"
python -m cea.analysis.sensitivity.sensitivity_demand_samples --samples-folder $SAMPLES_FOLDER -n $N \
          --method $METHOD --calc-second-order $CALC_SECOND_ORDER --num-levels $NUM_LEVELS \
          --variable-groups $VARIABLE_GROUPS
