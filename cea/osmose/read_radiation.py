import os
import pandas as pd
import numpy as np
from matplotlib import pyplot


def read_radiation():
    path_1 = "C:\\CEA_cases\\ABU_CBD_m_OFF_SG\\outputs\\data\\solar-radiation"
    path_1_demand = "C:\\CEA_cases\\ABU_CBD_m_OFF_SG\\outputs\\data\\demand"
    path_2 = "C:\\CEA_cases\\ABU_CBD_m\\outputs\\data\\solar-radiation"
    path_2_demand = "C:\\CEA_cases\\ABU_CBD_m\\outputs\\data\\demand"
    buildings = ["B001", "B002", "B003", "B004", "B005", "B006", "B007", "B008", "B009", "B010"]

    for building in buildings:
        print building
        sensors_rad_1 = pd.read_json(os.path.join(path_1, building + '_insolation_Whm2.json'))

        total_1 = float(sensors_rad_1.sum(0).sum())
        print sensors_rad_1.shape, total_1, "Wh/yr"
        #print total_1, "Wh/yr"
        sensors_metadata_1 = pd.read_csv(os.path.join(path_1, building + '_geometry.csv'))
        print sensors_metadata_1.shape, sensors_metadata_1['AREA_m2'].sum(), "m2"
        demand_1 = pd.read_csv(os.path.join(path_1_demand, building + '.csv'))



        #print sensors_metadata_1['AREA_m2'].sum(), "m2"
        sensors_rad_2 = pd.read_json(os.path.join(path_2, building + '_insolation_Whm2.json'))

        total_2 = float(sensors_rad_2.sum(0).sum())
        print sensors_rad_2.shape, total_2, "Wh/yr"
        #print total_2, "Wh/yr"
        sensors_metadata_2 = pd.read_csv(os.path.join(path_2, building + '_geometry.csv'))
        #print sensors_metadata_2.shape
        print sensors_metadata_2.shape, sensors_metadata_2['AREA_m2'].sum(), "m2"
        delta = ((total_1 - total_2)/total_1)*100
        print 'delta: ', delta, '%'
        demand_2 = pd.read_csv(os.path.join(path_2_demand, building + '.csv'))


        x_axis = np.arange(72)
        fig = pyplot.figure()
        time = '0_72'
        ax1 = fig.add_subplot(311)
        plot_radiation_compare(building, sensors_rad_1, sensors_rad_2, x_axis, time, ax1)
        ax2 = fig.add_subplot(312)
        plot_radiation_diff(building, sensors_rad_1, sensors_rad_2, x_axis, time, ax2)
        ax3 = fig.add_subplot(313)
        plot_demand_diff(building, demand_1, demand_2, x_axis, time, ax3)
        file_name = building + '_diff_' + time
        fig.savefig('C:\\CEA_cases\\ABU_CBD_m_OFF_SG\\' + file_name)

        # time = '5000_5072'
        # plot_radiation_compare(building, sensors_rad_1, sensors_rad_2, x_axis, time)
        # plot_radiation_diff(building, sensors_rad_1, sensors_rad_2, x_axis, time)
        # pyplot.show()
    return np.nan


def plot_radiation_compare(building, sensors_rad_1, sensors_rad_2, x_axis, time, ax):
    start_t = int(time.split('_')[0])
    end_t = int(time.split('_')[1])
    total_rad_1 = sensors_rad_1.sum(1).values[start_t:end_t]
    total_rad_2 = sensors_rad_2.sum(1).values[start_t:end_t]
    ax.bar(x_axis + 0.5, total_rad_1, alpha=0.5, label='in ABU')
    ax.bar(x_axis, total_rad_2, alpha=0.5, label='in SG')
    ax.legend(loc='upper right')
    pyplot.xlim(start_t, end_t)
    pyplot.xlabel('hour')
    pyplot.ylabel('irradiation')
    #file_name = building + '_compare_' + time
    #fig.savefig('C:\\CEA_cases\\ABU_CBD_m_OFF_SG\\' + file_name)
    return np.nan

def plot_radiation_diff(building, sensors_rad_1, sensors_rad_2, x_axis, time, ax):
    start_t = int(time.split('_')[0])
    end_t = int(time.split('_')[1])
    total_rad_1 = sensors_rad_1.sum(1).values[start_t:end_t].astype('float')
    total_rad_2 = sensors_rad_2.sum(1).values[start_t:end_t].astype('float')
    rad_compare = ((total_rad_1 - total_rad_2)/total_rad_1)*100
    #fig = pyplot.figure()
    ax.bar(x_axis, rad_compare, alpha=0.5, label='diff')
    ax.legend(loc='upper right')
    pyplot.xlim(start_t,end_t)
    pyplot.xlabel('hour')
    pyplot.ylabel('rad diff [%]')
    file_name = building + '_diff_' + time
    #fig.savefig('C:\\CEA_cases\\ABU_CBD_m_OFF_SG\\' + file_name)
    return np.nan

def plot_demand_diff(building, demand_1, demand_2, x_axis, time, ax):
    start_t = int(time.split('_')[0])
    end_t = int(time.split('_')[1])
    total_rad_1 = demand_1['QC_sys_kWh'].values[start_t:end_t].astype('float')
    total_rad_2 = demand_2['QC_sys_kWh'].values[start_t:end_t].astype('float')
    rad_compare = np.vectorize(divide_by_zero)(total_rad_1-total_rad_2,total_rad_1)
    #fig = pyplot.figure()
    ax.bar(x_axis, rad_compare, alpha=0.5, label='diff')
    ax.legend(loc='upper right')
    pyplot.xlim(start_t,end_t)
    pyplot.xlabel('hour')
    pyplot.ylabel('demand diff [%]')
    file_name = building + '_diff_' + time
    #fig.savefig('C:\\CEA_cases\\ABU_CBD_m_OFF_SG\\' + file_name)
    return np.nan


def divide_by_zero(n,d):
    return (n/d)*100 if d else float(0)

if __name__ == '__main__':
    read_radiation()
