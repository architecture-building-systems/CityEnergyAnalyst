to run radiation_main.py:

1.) install Daysim

2.) libraries to download:
    a.) conda install -c https://conda.anaconda.org/dlr-sc pythonocc-core=0.16  (compatible with py3dmodel)
    b.) install occutils: https://github.com/tpaviot/pythonocc-utils (store it to site-packages)
    c.) pip install pyshp
    d.) conda install lxml, networkx, pycollada

3.) additional information about py3dmodel/py2radiance
    https://github.com/chenkianwee/pyliburo
    https://chenkianwee.wordpress.com/low-exergy-design-method-environment/

4.) known issues: If the error message is: 'rtrace_dc: fatal - ("path"): truncated octree. It might be that daysim has
 problems with the scenario path. either because it is to long, includes twice the same folder name or spaces.
 On the other hand, the script will fail if the number of sensors is too high. modify the settings in this case

5.) Run daysim_main. the settings are stored in the config file.
