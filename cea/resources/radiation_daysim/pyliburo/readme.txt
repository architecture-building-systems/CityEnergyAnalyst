to run the environment:

1.) install anaconda for python2.7
instructions on how to use anaconda: http://conda.pydata.org/docs/using/envs.html

2.) libraries to download:
    a.) conda install lxml (version 3.5.0) (for reading citygml) (BSD) libxml2 and libxslt2 (MIT)
    b.) pip install pyshp (version 1.2.3) (for reading shapefiles) (mit license)
    c.) conda install -c https://conda.anaconda.org/dlr-sc pythonocc-core (cad kernel for all geometry operations) (GNU LGPL)
    d.) install occutils, https://github.com/tpaviot/pythonocc-utils/tree/master/OCCUtils, cut and paste into site-packages
    e.) conda install numpy (1.11.0) (BSD accepted license)
    f.) conda install scipy (0.17.0) (BSD accepted license)
    g.) easy_install pycollada (BSD)

3.) install Daysim from http://daysim.ning.com/ for the daylighting analysis
    a.) if c:/daysim/radiance/bin on env path, delete it
	
5.) conda install spyder (2.3.8) (for editing the scripts)