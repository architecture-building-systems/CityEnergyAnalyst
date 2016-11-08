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
    
## Running the scripts

### On Windows

Here is an example of running the scripts on windows. Replace paths according to your setup.

```bash
[esri104] darthoma@ITA-SCHLUE-W-17 C:\Users\darthoma\Documents\GitHub\CEAforArcGIS
> set PYTHONPATH=C:\Users\darthoma\Documents\GitHub\CEAforArcGIS;%PYTHONPATH%

[esri104] darthoma@ITA-SCHLUE-W-17 C:\Users\darthoma\Documents\GitHub\CEAforArcGIS
> md %TEMP%\samples
                                               
[esri104] darthoma@ITA-SCHLUE-W-17 C:\Users\darthoma\Documents\GitHub\CEAforArcGIS
> python cea\analysis\sensitivity\sensitivity_demand_samples.py --samples-folder "%TEMP%\samples" -n 1
created 12 samples in C:\Users\darthoma\AppData\Local\Temp\samples

[esri104] darthoma@ITA-SCHLUE-W-17 C:\Users\darthoma\Documents\GitHub\CEAforArcGIS
> dir %TEMP%\samples
 Volume in drive C has no label.
 Volume Serial Number is C84C-1BEB

 Directory of C:\Users\darthoma\AppData\Local\Temp\samples

03.11.2016  17:11    <DIR>          .
03.11.2016  17:11    <DIR>          ..
03.11.2016  17:11             1'943 problem.pickle
03.11.2016  17:11         1'056'080 samples.npy
               2 File(s)      1'058'023 bytes
               2 Dir(s)  528'840'749'056 bytes free
                                                                                         
[esri104] darthoma@ITA-SCHLUE-W-17 C:\Users\darthoma\Documents\GitHub\CEAforArcGIS       
> md %TEMP%\simulations

[esri104] darthoma@ITA-SCHLUE-W-17 C:\Users\darthoma\Documents\GitHub\CEAforArcGIS
> python cea\analysis\sensitivity\sensitivity_demand_simulate.py -i 0 -n 12 --scenario "C:\reference-case-open\baseline" --samples-folder %TEMP%\samples --simulation-folder %TEMP%\simulation --weather .\cea\databases\CH\Weather\Zurich.epw
read input files
done
Using 8 CPU's
Building No. 1 completed out of 9
Building No. 2 completed out of 9
Building No. 3 completed out of 9
Building No. 4 completed out of 9
Building No. 5 completed out of 9
Building No. 6 completed out of 9
Building No. 7 completed out of 9
Building No. 8 completed out of 9
Building No. 9 completed out of 9
done - time elapsed: 5.32 seconds

# ... this is repeated 12 times...

[esri104] darthoma@ITA-SCHLUE-W-17 C:\Users\darthoma\Documents\GitHub\CEAforArcGIS
> dir %TEMP%\simulation
 Volume in drive C has no label.
 Volume Serial Number is C84C-1BEB

 Directory of C:\Users\darthoma\AppData\Local\Temp\simulation

28.10.2016  09:35    <DIR>          .
28.10.2016  09:35    <DIR>          ..
28.10.2016  09:35    <DIR>          inputs
28.10.2016  09:35    <DIR>          outputs
               0 File(s)              0 bytes
               4 Dir(s)  528'803'373'056 bytes free

[esri104] darthoma@ITA-SCHLUE-W-17 C:\Users\darthoma\Documents\GitHub\CEAforArcGIS
> dir %temp%\samples
 Volume in drive C has no label.
 Volume Serial Number is C84C-1BEB

 Directory of C:\Users\darthoma\AppData\Local\Temp\samples

04.11.2016  09:51    <DIR>          .
04.11.2016  09:51    <DIR>          ..
04.11.2016  09:34             1'943 problem.pickle
04.11.2016  09:49               329 result.0.csv
04.11.2016  09:49               330 result.1.csv
04.11.2016  09:51               330 result.10.csv
04.11.2016  09:51               330 result.11.csv
04.11.2016  09:49               330 result.2.csv
04.11.2016  09:49               330 result.3.csv
04.11.2016  09:50               330 result.4.csv
04.11.2016  09:50               330 result.5.csv
04.11.2016  09:50               331 result.6.csv
04.11.2016  09:50               331 result.7.csv
04.11.2016  09:50               319 result.8.csv
04.11.2016  09:50               330 result.9.csv
04.11.2016  09:34             1'136 samples.npy
              14 File(s)          7'029 bytes
               2 Dir(s)  528'819'286'016 bytes free

[esri104] darthoma@ITA-SCHLUE-W-17 C:\Users\darthoma\Documents\GitHub\CEAforArcGIS
> type %TEMP%\samples\result.0.csv
,QHf_MWhyr,QCf_MWhyr,Ef_MWhyr,QEf_MWhyr
0,381.043,18.824,156.259,556.126
1,381.21,19.017,156.256,556.482
2,381.068,18.86,156.256,556.184
3,381.175,19.12,156.256,556.551
4,381.338,19.943,156.249,557.53
5,380.992,18.899,156.249,556.14
6,381.998,21.714,156.336,560.048
7,381.367,20.169,156.255,557.792
8,0.0,0.0,0.0,0.0
```

The above steps run morris sampling with N=1, grid_jump=2 and num_levels=4, simulates
all the samples and stores the results back into the sampling directory.

On the Euler cluster, we can set N to a much higher number, say, 1000 and we would then
run `sensitivity_demand_simulate` multiple times, incrementing the `--sample-index`
parameter by `--number-of-simulations` each time. We need to choose `--number-of-simulations`
to fit the simulation count in the time slot of the node as the Euler cluster will kill
any process that runs longer than a fixed amount of time. Keeping it as large as possible
reduces the overhead of waiting for a node to pick up the job, so we will need to
experiment a bit here...

The next step is to run the analysis on the results. This is done in a single process.

```
[esri104] darthoma@ITA-SCHLUE-W-17 C:\Users\darthoma\Documents\GitHub\CEAforArcGIS
> python cea\analysis\sensitivity\sensitivity_demand_analyze.py --samples-folder %TEMP%\samples
```

### Running on Euler

#### Instllation of SALib on Euler

FIXME: move this to the dev docs

I can't get SALib to install with `pip install SALib` because the version of setuptools is just too old.
Instead do this:

```
[darthoma@euler06 ~]$ git clone https://github.com/SALib/SALib.git
Initialized empty Git repository in /cluster/home/darthoma/SALib/.git/
remote: Counting objects: 2769, done.
Receiving objects: 100% (2769/2769), 2.56 MiB | 1.34 MiB/s, done.
remote: Total 2769 (delta 0), reused 0 (delta 0), pack-reused 2769
Resolving deltas: 100% (1748/1748), done.
```

And update your `$PYTHONPATH` to include that folder.

- I cloned the reference case project to my home folder.
- run the data helper script:

```
[darthoma@euler05 ~]$ python -m cea.demand.preprocessing.properties -s /cluster/home/darthoma/cea-reference-case/reference -case-open/baseline/
[darthoma@euler05 ~]$ sh CEAforArcGIS/euler/create-samples.sh
created 12 samples in /cluster/scratch/darthoma/samples_morris_1
[darthoma@euler05 ~]$ sh CEAforArcGIS/euler/run-demand.sh
Generic job.
Job <31205729> is submitted to queue <normal.4h>.
```

This sets up the demand calculation to run in batch mode. You can use the command `bjobs` to view the list of jobs
still open - read up in the [Euler wiki](https://scicomp.ethz.ch/wiki/Using_the_batch_system) on how that works.

NOTE: the git lfs system is not installed on the cluster. I'm not going to bother installing it, instead, we copy
the radiation files manually using `scp` as [described in the cluster documentation](https://scicomp.ethz.ch/wiki/FAQ#What_is_the_recommended_way_to_transfer_files_from.2Fto_the_cluster.3F):

```
[esri104] C:\reference-case-open\baseline\outputs\data\solar-radiation>scp radiation.csv darthoma@euler.ethz.ch:~/cea-reference-case/reference-case-open/baseline/outputs/data/solar-radiation
[esri104] C:\reference-case-open\baseline\outputs\data\solar-radiation>scp properties_surfaces.csv darthoma@euler.ethz.ch:~/cea-reference-case/reference-case-open/baseline/outputs/data/solar-radiation
```

Then, run the demand script:

Running the whole thing using the euler scripts:

```
export N=100
export METHOD=sobol
sh euler/create-samples.sh
sh euler/run-demand.sh
# wait for all the jobs to complete
sh euler/analyze-simulations.sh
```


You can use this command to see how many simulations a job batch has done (`31300468` is the jobid, get that from `bjobs` or `bbjobs`):

```
bpeek 31300468 | grep elapsed | wc
```


#### compiling the `calc_tm.pyd` files...

I'm leaving this for another day...


