"""
===========================
Primary energy and CO2 emissions model algorithm for building operation
===========================
J. Fonseca  script development          26.08.15
D. Thomas   formatting and cleaning     27.08.15
D. Thomas   integration in toolbox      27.08.15
J. Fonseca  script redevelopment        19.04.16

"""
from __future__ import division
import pandas as pd
from geopandas import GeoDataFrame as gpdf
import inputlocator

reload(inputlocator)


def lca_operation(locator, Qww_flag, Qhs_flag, Qcs_flag, Qcdata_flag, Qcrefri_flag, Eal_flag, Eaux_flag, Epro_flag,
                  Edata_flag):
    """
    algorithm to calculate the primary energy and CO2 emissions of buildings
    according to the method used in the integrated model of
    Fonseca et al. 2015.
    Appl. energy. and the performance factors of ecobau.ch

    Parameters
    ----------
    :param InputLocator locator: an InputLocator instance set to the scenario to work on
    :param boolean Qww_flag: create a separate file with emissions due to hot water consumption?
    :param boolean Qhs_flag: create a separate file with emissions due to space heating?
    :param boolean Qcs_flag: create a get separate file with emissions due to space cooling?
    :param boolean Qcdata_flag: create a separate file with emissions due to servers cooling?
    :param boolean Qcrefri_flag: create a separate file with emissions due to refrigeration?
    :param boolean Eal_flag: create a separate file with emissions due to appliances and lighting?
    :param boolean Eaux_flag: create a separate file with emissions due to auxiliary electricity?
    :param boolean Epro_flag: create a separate file with emissions due to electricity in industrial processes?
    :param boolean Edata_flag: create a separate file with emissions due to electricity consumption in data centers?

    Returns
    -------
    total_LCA_operation:.csv
        csv file of yearly primary energy per building and energy service
        (i.e. heating, hot water, cooling, electricity)

    The following files are created by this script, depending on which flags were set:

    - Qhs_LCA_operation:.csv
        describes the emissions and primary energy due to space heating
    - Qww_LCA_operation:.csv
        describes the emissions and primary energy due to domestic hot water consumption
    - Qcs_LCA_operation:.csv
        describes the emissions and primary energy due to space cooling
    - Qcdata_LCA_operation:.csv
        describes the emissions and primary energy due to servers cooling
    - Qcrefri_LCA_operation:.csv
        describes the emissions and primary energy due to refrigeration
    - Eal_LCA_operation:.csv
        describes the emissions and primary energy due to appliances and lighting
    - Eaux_LCA_operation:.csv
        describes the emissions and primary energy due to auxiliary electricity
    - Epro_LCA_operation:.csv
        describes the emissions and primary energy due to electricity in industrial processes
    - Edata_LCA_operation:.csv
        describes the emissions and primary energy due to electricity consumption in data centers


    """

    # local files
    demand = pd.read_csv(locator.get_total_demand())
    supply_systems = gpdf.from_file(locator.get_building_supply()).drop('geometry', axis=1)
    data_LCI = locator.get_life_cycle_inventory_supply_systems()
    factors_heating = pd.read_excel(data_LCI, sheetname='heating')
    factors_dhw = pd.read_excel(data_LCI, sheetname='dhw')
    factors_cooling = pd.read_excel(data_LCI, sheetname='cooling')
    factors_electricity = pd.read_excel(data_LCI, sheetname='electricity')

    # local variables
    QC_flag = E_flag = True # minmum output values
    result_folder = locator.get_lca_emissions_results_folder()

    # calculate total_LCA_operation:.csv
    heating = supply_systems.merge(demand,on='Name').merge(factors_heating, left_on='type_hs', right_on='code')
    dhw = supply_systems.merge(demand,on='Name').merge(factors_dhw, left_on='type_dhw', right_on='code')
    cooling = supply_systems.merge(demand,on='Name').merge(factors_cooling, left_on='type_cs', right_on='code')
    electricity = supply_systems.merge(demand,on='Name').merge(factors_electricity, left_on='type_el', right_on='code')

    # for heating services
    heating_services = [[Qhs_flag, 'Qhsf_MWhyr', 'Qhsf']]
    for x in heating_services:
        if x[0]:
            fields_to_plot = ['Name', x[2] + '_pen_GJ', x[2] + '_ghg_ton', x[2] + '_pen_MJm2', x[2] + '_ghg_kgm2']
            heating[fields_to_plot[1]] = heating[x[1]] * heating['PEN'] * 3.6
            heating[fields_to_plot[2]] = heating[x[1]] * heating['CO2'] * 3.6
            heating[fields_to_plot[3]] = heating[x[1]] * heating['PEN'] * 3600/heating['Af_m2']
            heating[fields_to_plot[4]] =  heating[x[1]] * heating['CO2'] * 3600/heating['Af_m2']
            heating[fields_to_plot].to_csv(result_folder+'\\' +x[2]+'_LCA_operation.csv',index=False,
                                           float_format='%.2f')

    # for dhw services
    dhw_services = [[Qww_flag, 'Qwwf_MWhyr', 'Qwwf']]
    for x in dhw_services:
        if x[0]:
            fields_to_plot = ['Name', x[2] + '_pen_GJ', x[2] + '_ghg_ton', x[2] + '_pen_MJm2', x[2] + '_ghg_kgm2']
            dhw[fields_to_plot[1]] = dhw[x[1]] * dhw['PEN'] * 3.6
            dhw[fields_to_plot[2]] = dhw[x[1]] * dhw['CO2'] * 3.6
            dhw[fields_to_plot[3]] = dhw[x[1]] * dhw['PEN'] * 3600 / dhw['Af_m2']
            dhw[fields_to_plot[4]] = dhw[x[1]] * dhw['CO2'] * 3600 / dhw['Af_m2']
            dhw[fields_to_plot].to_csv(result_folder + '\\' + x[2] + '_LCA_operation.csv', index=False,
                                       float_format='%.2f')
    # for cooling services
    cooling_services = [(QC_flag, 'QCf_MWhyr', 'QCf'), (Qcs_flag, 'Qcsf_MWhyr', 'Qcsf'),
                        (Qcdata_flag, 'Qcdataf_MWhyr', 'Qcdataf'), (Qcrefri_flag, 'Qcref_MWhyr', 'Qcref')]
    for x in cooling_services:
        if x[0]:
            fields_to_plot = ['Name', x[2] + '_pen_GJ', x[2] + '_ghg_ton', x[2] + '_pen_MJm2', x[2] + '_ghg_kgm2']
            cooling[fields_to_plot[1]] = cooling[x[1]] * cooling['PEN'] * 3.6
            cooling[fields_to_plot[2]] = cooling[x[1]] * cooling['CO2'] * 3.6
            cooling[fields_to_plot[3]] = cooling[x[1]] * cooling['PEN'] * 3600/cooling['Af_m2']
            cooling[fields_to_plot[4]] =  cooling[x[1]] * cooling['CO2'] * 3600/cooling['Af_m2']
            cooling[fields_to_plot].to_csv(result_folder+ '\\' + x[2] + '_LCA_operation.csv', index=False,
                                           float_format='%.2f')

    # for electrical services
    electrical_services = [(E_flag, 'Ef_MWhyr', 'Ef'), (Eal_flag, 'Ealf_MWhyr', 'Ealf'),
                           (Eaux_flag, 'Eauxf_MWhyr', 'Eauxf'), (Epro_flag, 'Eprof_MWhyr', 'Eprof'),
                           (Edata_flag, 'Edataf_MWhyr', 'Edataf')]
    for x in electrical_services:
        if x[0]:
            fields_to_plot = ['Name', x[2] + '_pen_GJ', x[2] + '_ghg_ton', x[2] + '_pen_MJm2', x[2] + '_ghg_kgm2']
            electricity[fields_to_plot[1]] = electricity[x[1]] * electricity['PEN'] * 3.6
            electricity[fields_to_plot[2]] = electricity[x[1]] * electricity['CO2'] * 3.6
            electricity[fields_to_plot[3]] = electricity[x[1]] * electricity['PEN'] * 3600/electricity['Af_m2']
            electricity[fields_to_plot[4]] =  electricity[x[1]] * electricity['CO2'] * 3600/electricity['Af_m2']
            electricity[fields_to_plot].to_csv(result_folder + '\\' + x[2] + '_LCA_operation.csv', index=False,
                                               float_format='%.2f')

    result = heating.merge(dhw, on='Name').merge(cooling, on='Name').merge(electricity, on='Name')
    result['pen_GJ'] = result['Qhsf_pen_GJ'] + result['Qwwf_pen_GJ'] + result['QCf_pen_GJ'] + result['Ef_pen_GJ']
    result['ghg_ton'] = result['Qhsf_ghg_ton'] + result['Qwwf_ghg_ton'] +result['QCf_ghg_ton'] + result['Ef_ghg_ton']
    result['pen_MJm2'] = result['Qhsf_pen_MJm2'] + result['Qwwf_pen_MJm2'] + result['QCf_pen_MJm2'] + result['Ef_pen_MJm2']
    result['ghg_kgm2'] = result['Qhsf_ghg_kgm2'] + result['Qwwf_ghg_kgm2'] + result['QCf_ghg_kgm2'] + result['Ef_ghg_kgm2']
    fields_to_plot = ['Name', 'pen_GJ', 'ghg_ton', 'pen_MJm2', 'ghg_kgm2']
    result[fields_to_plot].to_csv(locator.get_lca_operation(), index=False, float_format='%.2f')


def test_lca_operation():
    Qww_flag = Qhs_flag = True
    Qcs_flag = Qcdata_flag = Qcrefri_flag = True
    Eal_flag = Eaux_flag = Epro_flag = Edata_flag = True
    locator = inputlocator.InputLocator(scenario_path=r'C:\reference-case\baseline')
    lca_operation(locator=locator, Qww_flag=Qww_flag, Qhs_flag=Qhs_flag, Qcs_flag=Qcs_flag, Qcdata_flag=Qcdata_flag,
                  Qcrefri_flag=Qcrefri_flag, Eal_flag=Eal_flag, Eaux_flag=Eaux_flag, Epro_flag=Epro_flag,
                  Edata_flag=Edata_flag)

    print 'test_properties() succeeded'

if __name__ == '__main__':
    test_lca_operation()
