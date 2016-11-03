# Notes on running the sensitivity analysis on the Euler cluster

*NOTE*: You need to be an ETH Zurich affiliated person and own a nethz-account for access to the Euler cluster.

## Installation

See the contributor's manual for information on installing the software on Euler

## Main workflow

These are the steps to be performed for running the demand sensitivity analysis:

- create a set of "samples", i. e. a set of parameter configurations that are to be simulated
- run a demand simulation for each sample and store the output to the samples folder (see below)
  - copy reference case folder to simulation reference case folder
  - apply sample parameters to the reference case
- merge output data back to a single dataset
- run analysis on the output data

## File locations

The bash scripts make some assumptions on the installation of the CEA:

- the CEAforArcGIS repository is cloned to `$HOME/CEAforArcGIS`


The Euler cluster has [different filesystems](https://scicomp.ethz.ch/wiki/Data_management) for different purposes. 
Due to the way the simulation tasks are split up, the simulation uses the following folders:

- the reference case (`--scenario-path`) is used as a copy of the original reference case - each 
  sample is created from this case as a copy. You can keep the reference case anywhere you like in your 
  home folder or personal scratch storage.
  - home folder: `/cluster/home/username` (backed up, permanent)
  - personal scratch storage: `/cluster/scratch/username` (not backed up, deleted after 15 days)
  
- the weather path: the path to the *.epw file used for simulation. This can be kept in the home folder.
  
- the samples folder contains the inputs (list of samples and the problem statement) and the final outputs of the
  analysis. This should be stored in your personal scratch folder (as the home folder has a limit to 100k files).
  
- the simulation reference case is a copy of the original reference case with the variables from the sampling method
  applied to the input data. This folder is created by the demand simulation script and is stored in the local
  scratch folder of the node running the demand simulation.
  - local scratch storage: `/scratch` 
  - (actually, we will use the `$TMPDIR` function to ensure simultaneous simulations on the same node don't step on 
    each other's feet)
