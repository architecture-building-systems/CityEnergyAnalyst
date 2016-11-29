#!/usr/bin/env sh

# Runs the script `cea/analysis/sensitivity/sensitivity_demand_analyze.py` to analyze the output of the sensitivity
# simulations.
# Provides a handy interface using environment variables and default values tailored to the Euler cluster.

# Each parameter is set to the environment variable of the same name or the default value if not set.
# The samples folder is created if it doesn't yet exist.
# This is the mapping of environment variables to argument names of the `sensitivity_demand_analyze.py` script:
#
# environment variable | corresponding argument
# N                    | (not used, except for calculating the default $SAMPLES_FOLDER value)
# METHOD               | (not used, except for calculating the default $SAMPLES_FOLDER value)
# SAMPLES_FOLDER       | --samples-folder
# VARIABLE_GROUPS      | FIXME: not implemented yet

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
N=${N:-1000}
METHOD=${METHOD:-sobol}
SAMPLES_FOLDER=${SAMPLES_FOLDER:-${SCRATCH}/samples_${METHOD}_${N}}
VARIABLE_GROUPS=${VARIABLE_GROUPS:-VARIABLE_GROUPS=${VARIABLE_GROUPS:-THERMAL ARCHITECTURE INDOOR_COMFORT INTERNAL_LOADS}}   # FIXME: not implemented yet

mkdir -p $SAMPLES_FOLDER

# create the samples
python -m cea.analysis.sensitivity.sensitivity_demand_analyze --samples-folder $SAMPLES_FOLDER
