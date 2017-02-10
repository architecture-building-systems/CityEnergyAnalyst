"""
Solar graphs
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_graph_I_sol(hourlydata_groups):

    isolation = hourlydata_groups.rename(columns={0: 'Group 1', 1: 'Group 3', 2: 'Group 2'})

    fig, axes = plt.subplots(nrows = 2, ncols = 2, figsize=(32, 16), dpi=4200)
    ax1 = axes[0,0]; ax2 = axes[0,1]; ax3 = axes[1,0]; ax4 = axes[1,1]
    isolation.plot(ax = ax1); ax1.set_title('Year',fontsize=25); ax1.set_ylabel('Solar isolation (W/m2)',fontsize=20);ax1.set_xlabel('Hour of the year',fontsize=20);ax1.tick_params(axis='x', labelsize=20);ax1.tick_params(axis='y', labelsize=20);ax1.legend(fontsize=20)
    isolation[4000:4200].plot(ax = ax2, legend =False, antialiased=True); ax2.set_title('Summer',fontsize=25); ax2.set_ylabel('Solar isolation (W/m2)',fontsize=20);ax2.set_xlabel('Hour of the year',fontsize=20);ax2.tick_params(axis='x', labelsize=20);ax2.tick_params(axis='y', labelsize=20)
    isolation[1600:1800].plot(ax = ax3, legend =False, antialiased=True); ax3.set_title('Intermediate season',fontsize=25); ax3.set_ylabel('Solar isolation (W/m2)',fontsize=20);ax3.set_xlabel('Hour of the year',fontsize=20);ax3.tick_params(axis='x', labelsize=20);ax3.tick_params(axis='y', labelsize=20)
    isolation[8300:8500].plot(ax = ax4, legend =False, antialiased=True); ax4.set_title('Winter',fontsize=25); ax4.set_ylabel('Solar isolation (W/m2)',fontsize=20);ax4.set_xlabel('Hour of the year',fontsize=20);ax4.tick_params(axis='x', labelsize=20);ax4.tick_params(axis='y', labelsize=20)

    return

def calc_graph_PV(results,results_perarea):

    PV_production = pd.DataFrame({'Group 1':results[0],'Group 2':results[2],'Group 3':results[1], 'Total':(results[0]+results[1]+results[2])})
    PV_production_perarea = pd.DataFrame({'Group 1':results_perarea[0]*1000,'Group 2':results_perarea[2]*1000,'Group 3':results_perarea[1]*1000})
    fig, axes = plt.subplots(nrows = 2, ncols = 2, figsize=(32, 16), dpi=4200)
    ax1 = axes[0,0]; ax2 = axes[0,1]; ax3 = axes[1,0]; ax4 = axes[1,1]
    PV_production_perarea.plot(ax = ax1); ax1.set_title('Year',fontsize=25); ax1.set_ylabel('PV specific potential (W/m2)',fontsize=20);ax1.set_xlabel('Hour of the year',fontsize=20);ax1.tick_params(axis='x', labelsize=20);ax1.tick_params(axis='y', labelsize=20);ax1.legend(fontsize=20)
    PV_production_perarea[4000:4200].plot(ax = ax2, legend =False, antialiased=True); ax2.set_title('Summer',fontsize=25); ax2.set_ylabel('PV specific potential (W/m2)',fontsize=20);ax2.set_xlabel('Hour of the year',fontsize=20);ax2.tick_params(axis='x', labelsize=20);ax2.tick_params(axis='y', labelsize=20)
    PV_production_perarea[1600:1800].plot(ax = ax3, legend =False, antialiased=True); ax3.set_title('Intermediate season',fontsize=25); ax3.set_ylabel('PV specific potential (W/m2)',fontsize=20);ax3.set_xlabel('Hour of the year',fontsize=20);ax3.tick_params(axis='x', labelsize=20);ax3.tick_params(axis='y', labelsize=20)
    PV_production_perarea[8300:8500].plot(ax = ax4, legend =False, antialiased=True); ax4.set_title('Winter',fontsize=25); ax4.set_ylabel('PV specific potential (W/m2)',fontsize=20);ax4.set_xlabel('Hour of the year',fontsize=20);ax4.tick_params(axis='x', labelsize=20);ax4.tick_params(axis='y', labelsize=20)

    fig, axes = plt.subplots(nrows = 2, ncols = 2, figsize=(32, 16), dpi=4200)
    ax1 = axes[0,0]; ax2 = axes[0,1]; ax3 = axes[1,0]; ax4 = axes[1,1]
    PV_production.plot(ax = ax1); ax1.set_title('Year',fontsize=25); ax1.set_ylabel('PV potential (kW)',fontsize=20);ax1.set_xlabel('Hour of the year',fontsize=20);ax1.tick_params(axis='x', labelsize=20);ax1.tick_params(axis='y', labelsize=20);ax1.legend(fontsize=20)
    PV_production[4000:4200].plot(ax = ax2, legend =False, antialiased=True); ax2.set_title('Summer',fontsize=25); ax2.set_ylabel('PV potential (kW)',fontsize=20);ax2.set_xlabel('Hour of the year',fontsize=20);ax2.tick_params(axis='x', labelsize=20);ax2.tick_params(axis='y', labelsize=20)
    PV_production[1600:1800].plot(ax = ax3, legend =False, antialiased=True); ax3.set_title('Intermediate season',fontsize=25); ax3.set_ylabel('PV potential (kW)',fontsize=20);ax3.set_xlabel('Hour of the year',fontsize=20);ax3.tick_params(axis='x', labelsize=20);ax3.tick_params(axis='y', labelsize=20)
    PV_production[8300:8500].plot(ax = ax4, legend =False, antialiased=True); ax4.set_title('Winter',fontsize=25); ax4.set_ylabel('PV potential (kW)',fontsize=20);ax4.set_xlabel('Hour of the year',fontsize=20);ax4.tick_params(axis='x', labelsize=20);ax4.tick_params(axis='y', labelsize=20)

    return

def calc_graph_SC(result ,prop_observers, number_points, Tin):

    Area_group1 = prop_observers.loc[0,'area_netpv']*number_points[0]
    Area_group2 = prop_observers.loc[1,'area_netpv']*number_points[1]
    Area_group3 = prop_observers.loc[2,'area_netpv']*number_points[2]

    SC_production = pd.DataFrame({'Group 1':result[0][1]/Area_group1*1000,'Group 2':result[2][1]/Area_group3*1000,'Group 3':result[1][1]/Area_group2*1000})
    fig, axes = plt.subplots(nrows = 2, ncols = 2, figsize=(32, 16), dpi=4200)
    ax1 = axes[0,0]; ax2 = axes[0,1]; ax3 = axes[1,0]; ax4 = axes[1,1]
    SC_production.plot(ax = ax1, ylim=([0,600])); ax1.set_title('Year',fontsize=25); ax1.set_ylabel('SC specific potential (W/m2)',fontsize=20);ax1.set_xlabel('Hour of the year',fontsize=20);ax1.tick_params(axis='x', labelsize=20);ax1.tick_params(axis='y', labelsize=20);ax1.legend(fontsize=20)
    SC_production[4000:4200].plot(ax = ax2, legend =False, antialiased=True, ylim=([0,600])); ax2.set_title('Summer',fontsize=25); ax2.set_ylabel('SC specific potential (W/m2)',fontsize=20);ax2.set_xlabel('Hour of the year',fontsize=20);ax2.tick_params(axis='x', labelsize=20);ax2.tick_params(axis='y', labelsize=20)
    SC_production[1600:1800].plot(ax = ax3, legend =False, antialiased=True, ylim=([0,200])); ax3.set_title('Intermediate season',fontsize=25); ax3.set_ylabel('SC specific potential (W/m2)',fontsize=20);ax3.set_xlabel('Hour of the year',fontsize=20);ax3.tick_params(axis='x', labelsize=20);ax3.tick_params(axis='y', labelsize=20)
    SC_production[8300:8500].plot(ax = ax4, legend =False, antialiased=True); ax4.set_title('Winter',fontsize=25); ax4.set_ylabel('SC specific potential (W/m2)',fontsize=20);ax4.set_xlabel('Hour of the year',fontsize=20);ax4.tick_params(axis='x', labelsize=20);ax4.tick_params(axis='y', labelsize=20)


    SC_production = pd.DataFrame({'Group 1':result[0][1],'Group 2':result[2][1],'Group 3':result[1][1], 'Total':(result[0][1]+result[2][1]+result[1][1])})

    fig, axes = plt.subplots(nrows = 2, ncols = 2, figsize=(32, 16), dpi=4200)
    ax1 = axes[0,0]; ax2 = axes[0,1]; ax3 = axes[1,0]; ax4 = axes[1,1]
    SC_production.plot(ax = ax1, ylim=([0,25000])); ax1.set_title('Year',fontsize=25); ax1.set_ylabel('SC potential (kW)',fontsize=20);ax1.set_xlabel('Hour of the year',fontsize=20);ax1.tick_params(axis='x', labelsize=20);ax1.tick_params(axis='y', labelsize=20);ax1.legend(fontsize=20)
    SC_production[4000:4200].plot(ax = ax2, legend =False, antialiased=True, ylim=([0,25000])); ax2.set_title('Summer',fontsize=25); ax2.set_ylabel('SC potential (kW)',fontsize=20);ax2.set_xlabel('Hour of the year',fontsize=20);ax2.tick_params(axis='x', labelsize=20);ax2.tick_params(axis='y', labelsize=20)
    SC_production[1600:1800].plot(ax = ax3, legend =False, antialiased=True, ylim=([0,8000])); ax3.set_title('Intermediate season',fontsize=25); ax3.set_ylabel('SC potential (kW)',fontsize=20);ax3.set_xlabel('Hour of the year',fontsize=20);ax3.tick_params(axis='x', labelsize=20);ax3.tick_params(axis='y', labelsize=20)
    SC_production[8300:8500].plot(ax = ax4, legend =False, antialiased=True); ax4.set_title('Winter',fontsize=25); ax4.set_ylabel('PV potential (kW)',fontsize=20);ax4.set_xlabel('Hour of the year',fontsize=20);ax4.tick_params(axis='x', labelsize=20);ax4.tick_params(axis='y', labelsize=20)

    Toutvector = np.nan_to_num(np.divide((result[0][1]+result[2][1]+result[1][1]),(result[0][5]+result[2][5]+result[1][5])) + Tin)
    SC_production = pd.DataFrame({'Group 1':result[0][1],'Group 2':result[2][1],'Group 3':result[1][1], 'Total':(result[0][1]+result[2][1]+result[1][1])})
    SC_losses = pd.DataFrame({'Group 1':result[0][0],'Group 2':result[2][0],'Group 3':result[1][0], 'Total':(result[0][0]+result[2][0]+result[1][0])})
    SC_aux = pd.DataFrame({'Group 1':result[0][2],'Group 2':result[2][2],'Group 3':result[1][2], 'Total':(result[0][2]+result[2][2]+result[1][2])})
    SC_Tout = pd.DataFrame({'Group 1':result[0][3],'Group 2':result[2][3],'Group 3':result[2][3], 'Total':Toutvector})
    SC_mcp = pd.DataFrame({'Group 1':result[0][5],'Group 2':result[2][5],'Group 3':result[1][5], 'Total':(result[0][5]+result[2][5]+result[1][5])})

    # <codecell>

    fig, axes = plt.subplots(nrows = 2, ncols = 2, figsize=(32, 16), dpi=4200)
    ax1 = axes[0,0]; ax2 = axes[0,1]; ax3 = axes[1,0]; ax4 = axes[1,1]
    SC_production.plot(ax = ax1, ylim=([0,20000])); ax1.set_title('Thermal Output',fontsize=25); ax1.set_ylabel('SC potential (kW)',fontsize=20);ax1.set_xlabel('Hour of the year',fontsize=20);ax1.tick_params(axis='x', labelsize=20);ax1.tick_params(axis='y', labelsize=20);ax1.legend(fontsize=20)
    SC_losses.plot(ax = ax2, legend =False, antialiased=True, ylim=([0,1000])); ax2.set_title('Thermal Losses',fontsize=25); ax2.set_ylabel('losses (kW)',fontsize=20);ax2.set_xlabel('Hour of the year',fontsize=20);ax2.tick_params(axis='x', labelsize=20);ax2.tick_params(axis='y', labelsize=20)
    SC_aux.plot(ax = ax3, legend =False, antialiased=True, ylim=([0,200])); ax3.set_title('Auxiliary electricity',fontsize=25); ax3.set_ylabel('Eaux (kW)',fontsize=20);ax3.set_xlabel('Hour of the year',fontsize=20);ax3.tick_params(axis='x', labelsize=20);ax3.tick_params(axis='y', labelsize=20)
    SC_Tout.plot(ax = ax4, legend =False, antialiased=True); ax4.set_title('Return temperature',fontsize=25); ax4.set_ylabel('Tout (C)',fontsize=20);ax4.set_xlabel('Hour of the year',fontsize=20);ax4.tick_params(axis='x', labelsize=20);ax4.tick_params(axis='y', labelsize=20)

    return

def calc_graph_SC(result, Tin):

    Toutvector = np.nan_to_num(np.divide((result[0][1]+result[2][1]+result[1][1]),(result[0][5]+result[2][5]+result[1][5])) + Tin)
    PVT_thermal_gen = pd.DataFrame({'Group 1':result[0][1],'Group 2':result[2][1],'Group 3':result[1][1], 'Total':(result[0][1]+result[2][1]+result[1][1])})
    PVT_losses = pd.DataFrame({'Group 1':result[0][0],'Group 2':result[2][0],'Group 3':result[1][0], 'Total':(result[0][0]+result[2][0]+result[1][0])})
    PVT_aux = pd.DataFrame({'Group 1':result[0][2],'Group 2':result[2][2],'Group 3':result[1][2], 'Total':(result[0][2]+result[2][2]+result[1][2])})
    PVT_Tout = pd.DataFrame({'Group 1':result[0][3],'Group 2':result[2][3],'Group 3':result[2][3], 'Total':Toutvector})
    PVT_mcp = pd.DataFrame({'Group 1':result[0][5],'Group 2':result[2][5],'Group 3':result[1][5], 'Total':(result[0][5]+result[2][5]+result[1][5])})
    PVT_electrical_gen = pd.DataFrame({'Group 1':result[0][6],'Group 2':result[2][6],'Group 3':result[1][6], 'Total':(result[0][6]+result[2][6]+result[1][6])})

    # <codecell>

    fig, axes = plt.subplots(nrows = 3, ncols = 2, figsize=(32, 24), dpi=4200)
    ax1 = axes[0,0]; ax2 = axes[0,1]; ax3 = axes[1,0]; ax4 = axes[1,1]; ax5 = axes[2,0]; ax6 = axes[2,1]
    PVT_thermal_gen.plot(ax = ax1, ylim=([0,30000])); ax1.set_title('Thermal Output',fontsize=25); ax1.set_ylabel(r'$\Phi_{PVT,th}$'+'  (kW)',fontsize = 30 );ax1.set_xlabel('Hour of the year',fontsize=20);ax1.tick_params(axis='x', labelsize=20);ax1.tick_params(axis='y', labelsize=20);ax1.legend(fontsize=20)
    PVT_losses.plot(ax = ax2, legend =False, antialiased=True, ylim=([0,400])); ax2.set_title('Distribution thermal Losses',fontsize=25); ax2.set_ylabel(r'$\Phi_{PVT,dis,l}$'+'  (kW)',fontsize = 30 );ax2.set_xlabel('Hour of the year',fontsize=20);ax2.tick_params(axis='x', labelsize=20);ax2.tick_params(axis='y', labelsize=20)
    PVT_electrical_gen.plot(ax = ax3, legend =False, antialiased=True); ax3.set_title('Electrical Output',fontsize=25); ax3.set_ylabel(r'$\Phi_{PVT,e}$'+'  (kW)',fontsize = 30 );ax3.set_xlabel('Hour of the year',fontsize=20);ax3.tick_params(axis='x', labelsize=20);ax3.tick_params(axis='y', labelsize=20)
    PVT_aux.plot(ax = ax4, legend =False, antialiased=True, ylim=([0,200])); ax4.set_title('Auxiliary electricity',fontsize=25); ax4.set_ylabel(r'$\Phi_{PVT,aux}$'+'  (kW)',fontsize = 30 );ax4.set_xlabel('Hour of the year',fontsize=20);ax4.tick_params(axis='x', labelsize=20);ax4.tick_params(axis='y', labelsize=20)
    PVT_mcp.plot(ax = ax5, legend =False, antialiased=True); ax5.set_title('Capacity mass flow rate',fontsize=25); ax5.set_ylabel(r'$\.{mCp}$'+'  (kW/C)',fontsize = 30 );ax5.set_xlabel('Hour of the year',fontsize=20);ax5.tick_params(axis='x', labelsize=20);ax5.tick_params(axis='y', labelsize=20)
    PVT_Tout.plot(ax = ax6, legend =False, antialiased=True); ax6.set_title('Return temperature',fontsize=25); ax6.set_ylabel(r'$\mathit{T_{PVT, out}}$'+'  (kW)',fontsize = 30 );ax6.set_xlabel('Hour of the year',fontsize=20);ax6.tick_params(axis='x', labelsize=20);ax6.tick_params(axis='y', labelsize=20)

    return
