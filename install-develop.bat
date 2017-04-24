conda create -n cea python=2.7
activate cea
conda install -c conda-forge -y geopandas ephem
conda install -c dlr-sc tbb freeimageplus gl2ps
conda install --c oce -c pythonocc -y pythonocc-core=0.17.3
