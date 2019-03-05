# CONCEPT - Connecting District Energy and Power Systems in Future Singaporean New Towns

## Prerequisites

1. Install Gurobi Optimizer. Gurobi has free license for Academic Users. the following link aids in obtaining the same 
(http://www.gurobi.com/registration/academic-license-reg)

2. Install the following packages in the `cea` environment (using anaconda prompt). Do note that the version number 
is essential for `pvlib`

        'pandas',
        'numpy',
        'CoolProp',
        'geopandas',
        'deap',
        'networkx',
        'matplotlib',
        'pyomo',
        'simpledbf',
        'xlrd',
        'scipy',
        'pvlib==0.5.2',
        'pyshp',
        'sqlalchemy',  # No real dependency, just to suppress warning
        'pandapower'
        
3. Fix Fiona/GDAL installation: https://github.com/architecture-building-systems/CityEnergyAnalyst/issues/1741
        1. Go to: https://www.lfd.uci.edu/~gohlke/pythonlibs/
        2. Download `Fiona‑1.8.4‑cp27‑cp27m‑win_amd64.whl` and `GDAL‑2.2.4‑cp27‑cp27m‑win_amd64.whl`
        3. Run `cd path_to_download_folder`
        4. Run `pip install Fiona-1.8.4-cp27-cp27m-win_amd64.whl --upgrade`
        5. Run `pip install GDAL-2.2.4-cp27-cp27m-win_amd64.whl --upgrade`