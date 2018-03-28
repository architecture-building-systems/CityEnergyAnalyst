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
    delete_pyd('..', 'demand', 'rc_model_sia_cc.pyd')
    delete_pyd('rc_model_sia_cc.pyd')
    compile_rc_model_sia()
    copy_pyd('rc_model_sia_cc.pyd', ['..', 'demand', 'rc_model_sia_cc.pyd'])
    delete_pyd('rc_model_sia_cc.pyd')

    delete_pyd('..', 'technologies', 'calc_radiator.pyd')
    delete_pyd('calc_radiator.pyd')
    compile_radiators()
    copy_pyd('calc_radiator.pyd', ['..', 'technologies', 'calc_radiator.pyd'])
    delete_pyd('calc_radiator.pyd')

    delete_pyd('..', 'technologies', 'storagetank_cc.pyd')
    delete_pyd('storagetank_cc.pyd')
    compile_storagetank()
    copy_pyd('storagetank_cc.pyd', ['..', 'technologies', 'storagetank_cc.pyd'])
    delete_pyd('storagetank_cc.pyd')


def delete_pyd(*pathspec):
    """Delete the file with the pathspec. `pathspec` is an array of path segments."""
    path_to_calc_tm_pyd = os.path.join(os.path.dirname(__file__), *pathspec)
    if os.path.exists(path_to_calc_tm_pyd):
        os.remove(path_to_calc_tm_pyd)

def copy_pyd(source, destination):
    parent = os.path.dirname(__file__)
    shutil.copy(os.path.join(parent, source),
                os.path.join(parent, *destination))


def compile_rc_model_sia():
    import cea.demand.rc_model_SIA
    reload(cea.demand.rc_model_SIA)
    cc = CC('rc_model_sia_cc')

    # cc.export('calc_h_ec', "f8(f8)")(cea.demand.rc_model_SIA.calc_h_ec)
    # cc.export('calc_h_ac', "f8(f8)")(cea.demand.rc_model_SIA.calc_h_ac)
    # cc.export('calc_h_ea', "f8(f8, f8, f8)")(cea.demand.rc_model_SIA.calc_h_ea)
    # cc.export('calc_f_sc', "f8(f8, f8, f8, f8)")(cea.demand.rc_model_SIA.calc_f_sc)
    cc.export('calc_phi_m', "f8(f8, f8, f8, f8, f8, f8, f8)")(cea.demand.rc_model_SIA.calc_phi_m)
    cc.export('calc_phi_c', "f8(f8, f8, f8, f8, f8, f8, f8)")(cea.demand.rc_model_SIA.calc_phi_c)
    cc.export('calc_theta_c', "f8(f8, f8, f8, f8, f8, f8, f8, f8, f8)")(cea.demand.rc_model_SIA.calc_theta_c)
    cc.export('calc_phi_m_tot', "f8(f8, f8, f8, f8, f8, f8, f8, f8, f8, f8, f8, f8)")(
        cea.demand.rc_model_SIA.calc_phi_m_tot)
    cc.export('calc_phi_a', "f8(f8, f8, f8, f8, f8)")(cea.demand.rc_model_SIA.calc_phi_a)
    cc.export('calc_theta_m', "f8(f8, f8)")(cea.demand.rc_model_SIA.calc_theta_m)
    cc.export('calc_h_ea', "f8(f8, f8, f8)")(cea.demand.rc_model_SIA.calc_h_ea)
    cc.export('calc_theta_m_t', "f8(f8, f8, f8, f8, f8)")(cea.demand.rc_model_SIA.calc_theta_m_t)
    cc.export('calc_theta_ea', "f8(f8, f8, f8, f8, f8)")(cea.demand.rc_model_SIA.calc_theta_ea)
    cc.export('calc_h_em', "f8(f8, f8)")(cea.demand.rc_model_SIA.calc_h_em)
    cc.export('calc_h_3', "f8(f8, f8)")(cea.demand.rc_model_SIA.calc_h_3)

    cc.compile()


def compile_radiators():
    import cea.technologies.radiators
    reload(cea.technologies.radiators)
    cc = CC('calc_radiator')

    cc.export('fh', "f8(f8, f8, f8, f8, f8, f8, f8)")(cea.technologies.radiators.fh)
    cc.export('lmrt', "f8(f8, f8, f8)")(cea.technologies.radiators.lmrt)

    cc.compile()


def compile_storagetank():
    import cea.technologies.storage_tank
    reload(cea.technologies.storage_tank)
    cc = CC('storagetank_cc')

    cc.export('ode', "f8(f8[:], f8, f8, f8, f8, f8, f8, f8)")(cea.technologies.storage_tank.ode)

    cc.compile()

if __name__ == '__main__':
    main()
