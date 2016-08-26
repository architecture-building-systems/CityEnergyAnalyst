"""
Compile the .pyd files using Numba pycc to speed up the calculation of certain modules.
Currently used for:

- calc_tm.pyd (used in demand/sensible_loads.py)
- calc_radiator.pyd (used in technologies/radiators.py)

In order to run this script, you will need to install Numba. Try: `conda install numba`
"""
from numba.pycc import CC
import shutil
import os


def main():
    delete_pyd('..', 'demand', 'calc_tm.pyd')
    delete_pyd('calc_tm.pyd')
    compile_sensible_loads()
    copy_pyd('calc_tm.pyd', ['..', 'demand', 'calc_tm.pyd'])
    delete_pyd('calc_tm.pyd')

    delete_pyd('..', 'technologies', 'calc_radiator.pyd')
    delete_pyd('calc_radiator.pyd')
    compile_radiators()
    copy_pyd('calc_radiator.pyd', ['..', 'technologies', 'calc_radiator.pyd'])
    delete_pyd('calc_radiator.pyd')


def delete_pyd(*pathspec):
    """Delete the file with the pathspec. `pathspec` is an array of path segments."""
    path_to_calc_tm_pyd = os.path.join(os.path.dirname(__file__), *pathspec)
    if os.path.exists(path_to_calc_tm_pyd):
        os.remove(path_to_calc_tm_pyd)

def copy_pyd(source, destination):
    parent = os.path.dirname(__file__)
    shutil.copy(os.path.join(parent, source),
                os.path.join(parent, *destination))


def compile_sensible_loads():
    import cea.demand.sensible_loads
    reload(cea.demand.sensible_loads)
    cc = CC('calc_tm')

    cc.export('calc_tm', "UniTuple(f8, 2)(f8, f8, f8, f8, f8)")(cea.demand.sensible_loads.calc_tm)
    cc.export('calc_ts', "f8(f8, f8, f8, f8, i4, f8, f8, f8, f8)")(cea.demand.sensible_loads.calc_ts)
    cc.export('calc_ts_tabs', "f8(f8, f8, f8, f8, i4, f8, f8, f8, f8)")(cea.demand.sensible_loads.calc_ts_tabs)
    cc.export('calc_ta', "f8(f8, f8, i4, f8, f8, f8)")(cea.demand.sensible_loads.calc_ta)
    cc.export('calc_ta_tabs', "f8(f8, f8, i4, f8, f8, f8)")(cea.demand.sensible_loads.calc_ta_tabs)
    cc.export('calc_top', "f8(f8, f8)")(cea.demand.sensible_loads.calc_top)
    cc.export('calc_Im_tot', "f8(f8, f8, f8, f8, f8, f8, f8, f8, i4, f8, f8)")(cea.demand.sensible_loads.calc_Im_tot)
    cc.export('calc_Im_tot_tabs', "f8(f8, f8, f8, f8, f8, f8, f8, f8, i4, f8, f8)")(cea.demand.sensible_loads.calc_Im_tot_tabs)

    cc.compile()


def compile_radiators():
    import cea.technologies.radiators
    reload(cea.technologies.radiators)
    cc = CC('calc_radiator')

    cc.export('fh', "f8(f8, f8, f8, f8, f8, f8, f8)")(cea.technologies.radiators.fh)
    cc.export('lmrt', "f8(f8, f8, f8)")(cea.technologies.radiators.lmrt)

    cc.compile()

if __name__ == '__main__':
    main()
