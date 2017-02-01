import os
import time
import numpy as np
import pandas as pd

from OCC import BRepGProp, GProp, BRep, TopoDS
from OCC.StlAPI import StlAPI_Reader, StlAPI_Writer
from OCC.TopAbs import TopAbs_REVERSED, TopAbs_FORWARD, TopAbs_OUT, TopAbs_WIRE, TopAbs_SOLID
from OCCUtils import face, Topology

import gml3dmodel
import interface2py3d
import py3dmodel
from py3dmodel import py2radiance

from multiprocessing import Process



def face_normal(occface, nr_faces):
    fc = face.Face(occface)
    centre_uv, centre_pt = fc.mid_point()
    normal_dir = fc.DiffGeom.normal(centre_uv[0], centre_uv[1])


    if occface.Orientation() == TopAbs_REVERSED:
        normal_dir = normal_dir.Reversed()


    normal = (normal_dir.X(), normal_dir.Y(), normal_dir.Z())

    return normal




def percentage(task, now, total):
    percent = round((float(now)/float(total))*100, 0)
    division = 5
    number = int(round(percent/division, 0))

    bar = number * ">" + (100 / division - number) * "_"
    if now == total:
        print "\r batch", str(task), bar, percent, "%",
    else:
        print "\r batch", str(task),bar, percent, "%",


def sensors_per_building_face_area(an_core, an_cores, aresults_path, acol_key):
    nr_sen_list = []
    for k in range(0, an_cores):
        file_path = os.path.join(aresults_path, "temp", "sen_year_" + str(k) + ".csv")
        with open(file_path, "r") as ins:
            exiting = 0
            for line in ins:
                if exiting == 0:
                    line = line.split(',')
                    nr_sen_list.append(len(line))
                    exiting = 1
                else:
                    break

    nr_sen_list = [int(k) for k in nr_sen_list]

    bui_id_df = pd.read_csv(os.path.join(aresults_path, 'bui_id_df.csv'), sep=',')

    st_sen = 0
    end_sen = 0
    sen_interval = range(an_cores)
    face_area = range(an_cores)
    for k in range(0, an_cores):
        int_sen_interval = []
        header = []
        end_sen += nr_sen_list[k]

        bui_id_df_batch = bui_id_df[acol_key][st_sen:end_sen].values.tolist()
        face_area[k] = bui_id_df["fac_area"][st_sen:end_sen].values.tolist()

        previous_name = bui_id_df_batch[0]
        # insert the starting integer
        int_sen_interval.append(0)
        header.append(bui_id_df_batch[0])
        for j in range(0, len(bui_id_df_batch)):
            actual_name = bui_id_df_batch[j]
            if actual_name != previous_name:
                int_sen_interval.append(j)
                header.append(bui_id_df_batch[j])
            previous_name = actual_name
        # insert last integer in batch
        int_sen_interval.append(j+1)

        sen_interval[k] = int_sen_interval

        st_sen += nr_sen_list[k]

    return sen_interval[an_core], face_area[an_core], nr_sen_list, header



def sensors_per_building_face_area1(an_core, an_cores, aresults_path, acol_key):

    bui_id_df = pd.read_csv(os.path.join(aresults_path, "temp", 'bui_id_df_' + str(an_core) + '.csv'))

    bui_id_df_batch = bui_id_df[acol_key].values.tolist()
    face_area = bui_id_df["fac_area"].values.tolist()
    sen_interval = []
    header =[]
    previous_name = bui_id_df_batch[0]

    # insert the starting integer
    sen_interval.append(0)
    header.append(bui_id_df_batch[0])

    for j in range(0, len(bui_id_df_batch)):
        actual_name = bui_id_df_batch[j]
        if actual_name != previous_name:
            sen_interval.append(j)
            header.append(bui_id_df_batch[j])
        previous_name = actual_name

    # insert last integer in batch
    sen_interval.append(j+1)

    return sen_interval, face_area, header


def concat_results(an_cores, aresults_path, aspatial_sum, atime_sum, achunk_size):
    time1 = time.clock()

    with open(os.path.join(aresults_path, aspatial_sum + "_" + atime_sum + ".csv"), 'w') as results_file:
        lines = True
        iterator = 0

        while lines is True:
            for j in range(an_cores):

                data = pd.read_csv(os.path.join(aresults_path, "temp", aspatial_sum + "_" + atime_sum + "_" + str(j) + ".csv"),
                                   sep=',', header=None, skiprows=iterator * achunk_size, nrows=achunk_size)
                if data.shape[0] != achunk_size:
                    lines = False
                if j == 0:
                    result = data
                else:
                    result = pd.concat([result, data], axis=1)
            result.to_csv(results_file, sep=',', header=None, index=None)
            #print "chunk", iterator, round((time.clock()-time1)/60,1), "min"
            iterator += 1
    print "coacenated", result.shape[1], aspatial_sum, "for", atime_sum
    results_file.close()


def time_sums(an_core, aresults_path, atime_average_list):

    print "time sums batch ", an_core

    # if txt file of output does not exist rename ill to txt
    illum_file_path = os.path.join(aresults_path, 'daysim_data' + str(an_core), 'res', 'daysim_data' + str(an_core))
    if not os.path.isfile(illum_file_path + '.txt'):
        filename = illum_file_path + '.ill'
        base_file, ext = os.path.splitext(filename)
        print filename
        os.rename(filename, base_file + ".txt")

    with open(illum_file_path + '.txt', "r") as ins:
        sens_nr = len(ins.readline().split())-3
        day_sum_0 = np.zeros([sens_nr])
        day_sum = day_sum_0
        daysinyear = 365

    # =============================== daily sums sensor file =============================== #

    days = ([])
    sen_hour_path = os.path.join(aresults_path, "temp", "sen_hour_" + str(an_core)+".csv")
    if os.path.exists(sen_hour_path):
        os.remove(sen_hour_path)

    sen_hour = open(sen_hour_path, 'ab')
    with open(illum_file_path + '.txt', "r") as ins:
        hourinyear = 1
        for line in ins:
            if hourinyear > daysinyear*24:
                # break the inner loop
                break
            else:
                sensor_series = line.split()
                sensor_series = [float(j) for j in sensor_series]
                sensor_series = np.array(sensor_series[3:])

                #if 'hour' in atime_average_list:
                write_line = str(sensor_series.tolist()).rstrip()
                write_line = write_line.replace('[', '')
                write_line = write_line.replace(']', '')
                sen_hour.write(write_line+'\n')

                # sensor_series = sensor_series.astype(int)
                day_sum = np.sum([day_sum, sensor_series], axis=0)
                if hourinyear % 24 == 0:
                    day = int(np.ceil(hourinyear/24))
                    days = np.append(days, day_sum, axis=0)
                    day_sum = day_sum_0
                    percentage(an_core, day, daysinyear)
            hourinyear += 1
    days = days.reshape((daysinyear, sens_nr))

    # =============================== monthly sums sensor file =============================== #
    sens_nr_new = len(days[0])
    monthday_list = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]
    months = ([])
    for k in range(0, 12):
        st_day = monthday_list[k]
        end_day = monthday_list[k+1]-1
        months = np.append(months, np.sum([days[st_day:end_day]], axis=1))
    months = months.reshape((12, sens_nr_new))

    # =============================== yearly sums sensor file =============================== #
    year = np.sum(days, axis=0)
    year = pd.DataFrame(year)
    year = year.T
    year.to_csv(os.path.join(aresults_path, "temp", "sen_year_" + str(an_core)+".csv"), index=None, header=None,
                sep=',', float_format='%.1f')

    np.savetxt(os.path.join(aresults_path, "temp", "sen_day_" + str(an_core)+".csv"), days, fmt='%1.1f', delimiter=",")
    np.savetxt(os.path.join(aresults_path, "temp", "sen_month_" + str(an_core)+".csv"), months, fmt='%1.1f', delimiter=",")


def sen_average(an_core, an_cores, aresults_path, aspatial_sum, atime_sum):
    if aspatial_sum == "sen":
        return
    sen_interval, face_area, header = sensors_per_building_face_area1(an_core, an_cores, aresults_path, aspatial_sum)
    sensor_file = os.path.join(aresults_path, "temp", "sen_" + atime_sum + "_" + str(an_core) + ".csv")
    sep = ','

    if atime_sum == "hour":
        time_steps = 8760
        sensor_file = os.path.join(aresults_path, 'daysim_data' + str(an_core), 'res', 'daysim_data' + str(an_core) +
                                   ".txt")
        sep = ' '
    if atime_sum == "day":
        time_steps = 365
    if atime_sum == "month":
        time_steps = 12
    if atime_sum == "year":
        time_steps = 1

    res_sum = np.zeros((time_steps, len(sen_interval)-1))

    with open(sensor_file, "r") as ins:
        hourinyear = 0
        for line in ins:
            sensor_series = line.split(sep)
            if atime_sum == "hour":
                sensor_series = [float(j) for j in sensor_series[4:]]
            else:
                sensor_series = [float(j) for j in sensor_series]

            sensor_series = np.array(sensor_series)

            for k in range(0, len(sen_interval)-1):
                # mean of W/m2 per sensor times m2 per face --> average kW per face
                res_sum[hourinyear, k] = np.mean(sensor_series[sen_interval[k]:sen_interval[k + 1]]) #*
                                                 #face_area[sen_interval[k]:sen_interval[k + 1]])/1000
            hourinyear += 1

    res_sum = pd.DataFrame(res_sum)
    res_sum.to_csv(os.path.join(aresults_path, "temp", aspatial_sum+"_"+atime_sum+"_" + str(an_core) + ".csv"),
                   header=None, index=False, float_format='%1.1f')

    print "batch ", an_core, len(sen_interval) - 1, aspatial_sum, atime_sum


def bui_zone_roof_average(an_core, an_cores, aresults_path, alist, atime_sum, achunk_size):
    import os
    import pandas as pd
    import math

    calc_speed = "fast"

    #sen_interval, dummy, nr_sen_list, header = sensors_per_building_face_area(an_core, an_cores, aresults_path, "bui")
    ffdegree = math.sqrt(2) / 2
    max_angle = math.sqrt(2) / 2
    zone_height = 3
    area_limit = 2

    # start and end row of each batch
    sensor_batch = pd.read_csv(os.path.join(aresults_path, "temp", 'bui_id_df_' + str(an_core) + '.csv'))
    bui_fac_list = sensor_batch["bui_fac"].tolist()
    bui_fac_area = sensor_batch["fac_area"].tolist()
    sen_area = sensor_batch["sen_area"].tolist()
    '''
    # number of sensors per face
    sen_nr = []
    for row_int in range(len(bui_fac_list)):
        sen_nr.append(bui_fac_list.count(bui_fac_list[row_int]))
        print row_int
    # average area per sensor
    sen_area = []
    for row_int in range(len(bui_fac_list)):
        sen_area.append(bui_fac_area[row_int]/sen_nr[row_int])
        print row_int
    # calculate min of z of all buildings
    '''
    building_min = sensor_batch[["bui", "sen_z"]].groupby("bui").min().reset_index()

    if calc_speed == "fast":
        sp_int = [0] * sensor_batch.shape[0]
        sg_int = [0] * sensor_batch.shape[0]
        for index, row in sensor_batch.iterrows():
            percentage("calc difference measures", index, sensor_batch.shape[0])
            # zoning with height
            building_name = sensor_batch["bui"][index]
            # solar potential
            if sensor_batch["fac_area"][index] > area_limit and sensor_batch["sen_dir_z"][index] > max_angle:
                sp_int[index] = 1
            # solar gains
            if building_name[-3:] != "rta":
                sg_int[index] = 1
        sensor_batch["sg_int"] = sg_int
        sensor_batch["sp_int"] = sp_int

        data_file = os.path.join(aresults_path, "temp", "sen_" + atime_sum + "_" + str(an_core) + ".csv")


        file_path_sp = os.path.join(aresults_path, "temp", "bui_sp_" + atime_sum + "_" + str(an_core) + ".csv")
        file_path_sg = os.path.join(aresults_path, "temp", "bui_sg_" + atime_sum + "_" + str(an_core) + ".csv")

        if os.path.exists(file_path_sp):
            os.remove(file_path_sp)
        if os.path.exists(file_path_sg):
            os.remove(file_path_sg)
        with open(file_path_sg, 'a') as results_file_sg:
            with open(file_path_sp, 'a') as results_file_sp:
                sensor_int = sensor_batch[["bui_sh", "sp_int", "sg_int"]]

                lines = True
                iterator = 0
                while lines is True:

                    percentage(str(an_core)+" bui_zone", iterator*achunk_size, 8760)

                    time1 = time.clock()

                    data = pd.read_csv(data_file, sep=',', header=None, skiprows=achunk_size * iterator, nrows=achunk_size)

                    if data.shape[0] != achunk_size:
                        lines = False

                    data = data.multiply(sen_area, axis=1).T.reset_index(drop=True)
                    all = pd.concat([sensor_int, data], axis=1)

                    all_sp = all.groupby(["bui_sh", "sp_int"]).sum().reset_index()
                    solar_pot = all_sp.loc[all_sp['sp_int'] == 1, list(all_sp.columns.values)[4:]].T
                    header_sp = all_sp.loc[all_sp['sp_int'] == 1, list(all_sp.columns.values)[0]]
                    solar_pot.columns = header_sp

                    all_sg = all.groupby(["bui_sh", "sg_int"]).sum().reset_index()
                    header_sg = all_sg.loc[all_sg['sg_int'] == 1, list(all_sg.columns.values)[0]]
                    solar_gains = all_sg.loc[all_sg['sg_int'] == 1, list(all_sg.columns.values)[4:]].T
                    solar_gains.columns = header_sg

                    header_bool = False
                    if iterator == 0:
                        header_bool = True

                    solar_pot.to_csv(results_file_sp, index=None, header=header_bool, sep=',', float_format='%1.1f')
                    solar_gains.to_csv(results_file_sg, index=None, header=header_bool, sep=',', float_format='%1.1f')

                    #print "save data", round((time.clock() - time1) / 60, 2), "min"


                    iterator += 1





    if calc_speed != "fast":
        zone_int = []
        dir_int = []
        rta_int = []
        bui_no = []
        area_int = []
        bui_int = 0

        for index, row in sensor_batch.iterrows():
            percentage("calc difference measures", index, sensor_batch.shape[0])
            # zoning with height
            building_name = sensor_batch["bui"][index]
            min_elevation = building_min["sen_z"].loc[building_min['bui'] == building_name]
            zone_int.append(round((sensor_batch["sen_z"][index] - min_elevation) / zone_height, 0))

            # direction N, E, S, W, up [1,2,3,4,5]
            if sensor_batch["sen_dir_z"][index] > max_angle:
                dir_int.append("V")
            elif sensor_batch["sen_dir_y"][index] >= ffdegree:
                dir_int.append("N")
            elif sensor_batch["sen_dir_x"][index] > ffdegree:
                dir_int.append("E")
            elif sensor_batch["sen_dir_y"][index] <= -ffdegree:
                dir_int.append("S")
            else:
                dir_int.append("W")

            # roof top attachments
            if building_name[-3:] == "rta":
                rta_int.append(1)
            else:
                rta_int.append(0)

            # area limit
            if sensor_batch["fac_area"][index] > area_limit:
                area_int.append(1)
            else:
                area_int.append(0)

            # building integer
            if index != 0:
                bui_no.append(bui_int)

                if sensor_batch["bui_sh"][index] == last_building_name:
                    bui_int += 0
                else:
                    bui_int += 1
            last_building_name = sensor_batch["bui_sh"][index]
        bui_no.append(bui_int)

        sensor_batch["bui_no"] = bui_no
        sensor_batch["rta_int"] = rta_int
        sensor_batch["dir_int"] = dir_int
        sensor_batch["zone_int"] = zone_int
        sensor_batch["area_int"] = area_int
        sensor_batch["sen_area"] = sen_area

        data_file = os.path.join(aresults_path, "temp", "sen_" + atime_sum + "_" + str(an_core) + ".csv")

        if "bui_sp" in alist:
            file_path = os.path.join(aresults_path, "temp", "bui_sp_"+atime_sum+"_" + str(an_core) + ".csv")
            if os.path.exists(file_path):
                os.remove(file_path)
            with open(file_path, 'a') as results_file:
                sensor_int = sensor_batch[["bui_sh", "bui_no", "dir_int", "area_int"]]
                lines = True
                iterator = 0
                while lines is True:
                    time1 = time.clock()

                    data = pd.read_csv(data_file, sep=',', header=None, skiprows=achunk_size*iterator, nrows=achunk_size)
                    print data.shape
                    if data.shape[0] != achunk_size:
                        lines = False

                    print "load data", round((time.clock()-time1)/60, 2), "min"
                    time1 = time.clock()

                    data = data.multiply(sen_area, axis=1).T.reset_index(drop=True)

                    all = pd.concat([sensor_int, data], axis=1)

                    all = all.groupby(["bui_sh", "bui_no", "dir_int", "area_int"]).sum().reset_index()
                    selection = all.loc[(all['dir_int'] == "V") & (all['area_int'] == 1), list(all.columns.values)[4:]].T
                    header = all.loc[(all['dir_int'] == "V") & (all['area_int'] == 1), list(all.columns.values)[0]]
                    selection.columns = header
                    header_bool = False
                    if iterator == 0:
                        header_bool = True
                    print "select data", round((time.clock() - time1) / 60, 2), "min"
                    time1 = time.clock()

                    selection.to_csv(results_file, index=None, header=header_bool, sep=',', float_format='%1.1f')

                    print "save data", round((time.clock() - time1) / 60, 2), "min"
                    time1 = time.clock()
                    iterator += 1

        if "bui_sg" in alist:
            file_path = os.path.join(aresults_path, "temp", "bui_sg_"+atime_sum+"_" + str(an_core) + ".csv")
            if os.path.exists(file_path):
                os.remove(file_path)
            with open(file_path, 'a') as results_file:
                sensor_int = sensor_batch[["bui_sh", "bui_no", "rta_int"]]
                lines = True
                iterator = 0
                while lines is True:
                    data = pd.read_csv(data_file, sep=',', header=None, skiprows=achunk_size*iterator, nrows=achunk_size)
                    if data.shape[0] != achunk_size:
                        lines = False
                    data = data.multiply(sen_area, axis=1).T.reset_index(drop=True)
                    all = pd.concat([sensor_int, data], axis=1)
                    all = all.groupby(["bui_sh", "bui_no", "rta_int"]).sum().reset_index()
                    selection = all.loc[all['rta_int'] == 0, list(all.columns.values)[3:]].T
                    header = all.loc[all['rta_int'] == 0, list(all.columns.values)[0]]
                    selection.columns = header
                    header_bool = False
                    if iterator == 0:
                        header_bool = True
                    selection.to_csv(results_file, index=None, header=header_bool, sep=',', float_format='%1.1f')
                    iterator += 1

    '''
    if "bui_sp" in alist:
        # calculate solar potential
        sensor_int = sensor_batch[["bui_sh", "bui_no", "dir_int", "area_int"]]
        all = pd.concat([sensor_int, data], axis=1)
        all = all.groupby(["bui_sh", "bui_no", "dir_int", "area_int"]).sum().reset_index()
        selection = all.loc[(all['dir_int'] == "V") & (all['area_int'] == 1), list(all.columns.values)[4:]].T
        header = all.loc[(all['dir_int'] == "V") & (all['area_int'] == 1), list(all.columns.values)[0]]
        selection.columns = header
        selection.to_csv(os.path.join(aresults_path, "temp", "bui_sp_"+atime_sum+"_" + str(an_core) + ".csv"),
                         index=None, header=True,  sep=',', float_format='%1.1f')

    if "bui_dir" in alist:
        # calculate facade directions
        sensor_int = sensor_batch[["bui_sh", "bui_no", "rta_int", "dir_int"]]
        all = pd.concat([sensor_int, data], axis=1)
        all = all.groupby(["bui_sh", "bui_no", "rta_int", "dir_int"]).sum().reset_index()
        selection = all.loc[(all['dir_int'] != "V") & (all['rta_int'] == 0), list(all.columns.values)[4:]].T
        header = all.loc[(all['dir_int'] != "V") & (all['rta_int'] == 0), list(all.columns.values)[0]]
        selection.columns = header
        selection.to_csv(os.path.join(aresults_path, "temp", "bui_dir_"+atime_sum+"_" + str(an_core) + ".csv"),
                    index=None, header=True,  sep=',', float_format='%.1f')
    if "bui_zone" in alist:
        # calculate zones
        sensor_int = sensor_batch[["bui_sh", "bui_no", "rta_int", "zone_int"]]
        all = pd.concat([sensor_int, data], axis=1)
        all = all.groupby(["bui_sh", "bui_no", "rta_int", "zone_int"]).sum().reset_index()
        selection = all.loc[all['rta_int'] == 0, list(all.columns.values)[3:]].T
        header = all.loc[all['rta_int'] == 0, list(all.columns.values)[0]]
        selection.columns = header
        selection.to_csv(os.path.join(aresults_path, "temp", "bui_zone_"+atime_sum+"_" + str(an_core) + ".csv"),
                   index=None, header=True,  sep=',', float_format='%.1f')
    if "bui_sg" in alist:
        # calculate solar gains
        sensor_int = sensor_batch[["bui_sh", "bui_no", "rta_int"]]
        all = pd.concat([sensor_int, data], axis=1)
        all = all.groupby(["bui_sh", "bui_no", "rta_int"]).sum().reset_index()
        selection = all.loc[all['rta_int'] == 0, list(all.columns.values)[3:]].T
        header = all.loc[all['rta_int'] == 0, list(all.columns.values)[0]]
        selection.columns = header
        selection.to_csv(os.path.join(aresults_path, "temp", "bui_sg_" + atime_sum + "_" + str(an_core) + ".csv"),
                   index=None, header=True, sep=',', float_format='%.1f')
    if "sen_sp" in alist:
        # calculate solar potential sensor
        sensor_int = sensor_batch[["bui_fac_sen", "dir_int", "area_int"]]
        all = pd.concat([sensor_int, data], axis=1)
        selection = all.loc[(all['dir_int'] == "V") & (all['area_int'] == 1), list(all.columns.values)[3:]].T
        header = all.loc[(all['dir_int'] == "V") & (all['area_int'] == 1), list(all.columns.values)[0]]
        selection.columns = header
        selection.to_csv(os.path.join(aresults_path, "temp", "sen_sp_"+atime_sum+"_" + str(an_core) + ".csv"),
                  index=None, header=True,  sep=',', float_format='%.1f')
    if "sen_sg" in alist:
        # calculate solar gains sensor
        sensor_int = sensor_batch[["bui_fac_sen", "rta_int"]]
        all = pd.concat([sensor_int, data], axis=1)
        selection = all.loc[all['rta_int'] == 0, list(all.columns.values)[2:]].T
        header = all.loc[all['rta_int'] == 0, list(all.columns.values)[0]]
        selection.columns = header
        selection.to_csv(os.path.join(aresults_path, "temp", "sen_sg_" + atime_sum + "_" + str(an_core) + ".csv"),
                   index=None, header=None, sep=',', float_format='%.3f')

    # save new sensor file
    sensor_batch.to_csv(os.path.join(aresults_path, "temp", "bui_id_df_" + str(an_core) + ".csv"), index=None,
                        header=True, sep=',', float_format='%.1f')

    '''





















def log(message, wordwrap, awrite_log, aresults_path):

    file_name = "log.txt"
    message = str(message).replace("'", "").replace('(', '').replace(')', '').replace(',', '')

    if awrite_log is True:
        with open(os.path.join(aresults_path, file_name), 'ab') as log_file:
            log_file.write('\n'+message+wordwrap)
            log_file.close()
    else:
        print message, wordwrap


def multiprocess(function, arguments, an_cores):
    processes = []
    for an_core in range(an_cores):
        argument_list = list(arguments)
        argument_list[0] = an_core
        arguments = tuple(argument_list)
        process = Process(target=function, args=arguments)
        process.start()
        processes.append(process)
    for process in processes:
        process.join()


def get_list(folder, ending):
    geo_name_list = []
    for afile in os.listdir(folder):
        if afile.endswith(ending):
            root, ext = os.path.splitext(afile)
            geo_name_list.append(root)
    return geo_name_list


def make_unique(original_list):
    unique_list = []
    [unique_list.append(obj) for obj in original_list if obj not in unique_list]
    return unique_list


def write_points(out_file, points_list):
    for point in points_list:
        s = str(point[0])+','+str(point[1])+','+str(point[2])
        out_file.write("%s\n" % s)


def geometry2radiance(arad, building_solids_lists, abui_mat_list):
    # parameters for the radiance

    # loop over all builings
    core_count = 0
    for building_solids in building_solids_lists:
        bcnt = 0
        for building_solid in building_solids:
            bface_list = py3dmodel.fetch.faces_frm_solid(building_solid)
            bf_cnt = 0
            for bface in bface_list:
                bface_pts = interface2py3d.pyptlist_frm_occface(bface)
                srfname = "building_srf" + str(bcnt) + str(bf_cnt)
                # just use pure white paint
                # srfmat = "RAL7023_concrete_gray_paint"
                srfmat = abui_mat_list[core_count][bcnt]
                py2radiance.RadSurface(srfname, bface_pts, srfmat, arad)
                bf_cnt += 1
            bcnt += 1
        core_count += 1


def terrain2radiance(arad, geo_solids, geo_faces, geo_mat_list, geo_name_list):
    geo_int = 0
    for geo_solid in geo_solids:
        fac_int = 0
        for geo_face in geo_faces[geo_int]:
            tface_pts = interface2py3d.pyptlist_frm_occface(geo_face)
            srfname = geo_name_list[geo_int] + str(fac_int)
            srfmat = geo_mat_list[geo_int]
            py2radiance.RadSurface(srfname, tface_pts, srfmat, arad)
            fac_int += 1


def generate_sensor_points(an_core, aresults_path, awrite_log, abui_name_list, face_list, normal_list, axdim, aydim, aoffset,
                           aroof_resolution_increase, amax_roof_angle):

    abui_name_list = abui_name_list[an_core]
    face_list = face_list[an_core]
    normal_list = normal_list[an_core]

    total_faces = 0
    total_sensors = 0
    sensor_pts = []
    sensor_dirs = []
    sensor_srf_list = []
    bui_id_df = []

    os.path.join(aresults_path, "temp",  "_points_" + str(an_core) + ".csv")

    # loop over all builings
    bcnt = 0
    for bui_name in abui_name_list:
        bui_sen_nr = []
        # abui_name_list, faces, points ,

        if bui_name.find("_") == -1:
            name_length = len(bui_name)
        else:
            name_length = bui_name.find("_")
        bui_name_short = bui_name[0:name_length]

        bui_face_list = face_list[bcnt]
        bui_normal_list = normal_list[bcnt]

        # face_list = shell_list[bcnt]
        # face_list = py3dmodel.fetch.faces_frm_solid(building_solid)
        # loop thru the faces in the solid


        fac_int = 0
        for f in bui_face_list:
            normal = bui_normal_list[fac_int]
            #normal = py3dmodel.calculate.face_normal(f)

            # increase resolution on roof tops
            if normal[2] >= amax_roof_angle:
                axdim = axdim/aroof_resolution_increase
                aydim = aydim/aroof_resolution_increase
            else:
                axdim = axdim
                aydim = aydim

            # generate sensor points for a surface, create sensor points,surfaces with divions of xdim and ydim of
            # the domain of f
            a_sensor_srfs, a_sensor_pts, a_sensor_dirs = gml3dmodel.generate_sensor_surfaces(f, axdim, aydim, aoffset, normal)


            fac_area = py3dmodel.calculate.face_area(f)

            # generate dataframe with building, face and sensor ID
            sen_int = 0
            for sen_dir in a_sensor_dirs:

                bui_id_df.append((bui_name, bui_name_short, fac_int, str(bui_name)+'_'+str(fac_int), sen_int,
                                  str(bui_name)+'_'+str(fac_int)+'_'+str(sen_int), fac_area,
                                  fac_area/len(a_sensor_dirs), a_sensor_pts[sen_int][0], a_sensor_pts[sen_int][1],
                                  a_sensor_pts[sen_int][2], normal[0], normal[1], normal[2]))
                sen_int += 1
            fac_int += 1
            bui_sen_nr.append(sen_int)
            if a_sensor_pts is not None:
                sensor_pts.extend(a_sensor_pts)
                sensor_dirs.extend(a_sensor_dirs)
                sensor_srf_list.extend(a_sensor_srfs)

        log(("batch", an_core, "Building", bcnt, ' ', bui_name, fac_int, "faces", sum(bui_sen_nr), "sensors"), '',
            awrite_log, aresults_path)

        bcnt += 1
        # print bui_id

        total_faces = total_faces + fac_int
        total_sensors = total_sensors + sum(bui_sen_nr)
    log("----------------------------------------------", '', awrite_log, aresults_path)
    log(("batch", an_core, "total:", bcnt, "buildings", total_faces, "faces", total_sensors, "sensors"), "\n",
        awrite_log, aresults_path)

    bui_id_df = pd.DataFrame(bui_id_df,
                             columns=['bui', 'bui_sh', 'fac', 'bui_fac', 'sen_int', 'bui_fac_sen', 'fac_area',
                                      'sen_area', 'sen_x', 'sen_y',
                                      'sen_z', 'sen_dir_x', 'sen_dir_y', 'sen_dir_z'])

    bui_id_df.to_csv(os.path.join(aresults_path, "temp", 'bui_id_df_'+str(an_core)+'.csv'))
    # points_file.close()
    '''
    sensor_pts_df = pd.DataFrame(sensor_pts)
    sensor_pts_df.to_csv(os.path.join(aresults_path,'sensor_pts_df.csv'))
    sensor_dirs_df = pd.DataFrame(sensor_dirs)
    sensor_dirs_df.to_csv(os.path.join(aresults_path,'sensor_dirs_df.csv'))
    '''
    return sensor_pts, sensor_dirs


def execute_cumulative_rtrace(self, aab, pointsfilename):
    if self.cumulative_oconv_file_path is None:
        raise Exception
    # execute rtrace
    cur_dir = os.getcwd()
    os.chdir(self.data_folder_path)
    self.create_sensor_input_file(pointsfilename)
    cumulative_result_file_path = os.path.join(self.data_folder_path, "cumulative_radmap_results.txt")
    command = "rtrace -af ambientfile -n 8 -I -h -dp 2048 -ms 0.063 -ds .2 -dt .05 -dc .75 -dr 3 -st .01 -lr 12 " \
              "-lw .0005 -ab " + aab + " -ad 1000 -as 20 -ar 300 -aa 0.1   " + \
              self.cumulative_oconv_file_path + " " + " < " + self.sensor_file_path + \
              " " + " > " + " " + cumulative_result_file_path
    f = open(self.command_file, "a")
    f.write(command)
    f.write("\n")
    f.close()
    os.system(command)  # EXECUTE!!
    os.chdir(cur_dir)
    self.cumulative_result_file_path = cumulative_result_file_path


def execute_daysim(an_core, aresults_path, awrite_log, arad, aweatherfilepath, arad_n, arad_af, arad_ab, arad_ad,
                   arad_as, arad_ar, arad_aa,
                   arad_lr, arad_st, arad_sj, arad_lw, arad_dj, arad_ds, arad_dr, arad_dp):
    log(("batch", an_core), '', awrite_log, aresults_path)

    bui_id_df = pd.read_csv(os.path.join(aresults_path, "temp", 'bui_id_df_'+str(an_core)+'.csv'))

    sensor_pts = bui_id_df[["sen_x", "sen_y", "sen_z"]].values.tolist()
    sensor_dirs = bui_id_df[["sen_dir_x", "sen_dir_y", "sen_dir_z"]].values.tolist()

    nr_sen_list = []

    # generate daysim result folders for all an_cores
    daysim_dir = os.path.join(aresults_path, 'daysim_data'+str(an_core))
    arad.initialise_daysim(daysim_dir)
    # transform weather file
    arad.execute_epw2wea(aweatherfilepath)
    arad.execute_radfiles2daysim()

    # set simulation parameters the default settings are the complex scene 1 settings of daysimPS
    # rad.write_default_radiance_parameters()
    arad.write_radiance_parameters(arad_n, arad_af, arad_ab, arad_ad, arad_as, arad_ar, arad_aa, arad_lr, arad_st,
                                  arad_sj, arad_lw, arad_dj, arad_ds, arad_dr, arad_dp)
    '''
    # set sensor lists that increases the size to include only whole sensor sets
    pre_list_int = int(round(len(sensor_pts)/n_cores, 0))*(i+1)


    current_bui_name = ""
    last_bui_name = ""

    # for all cores besides last one search for last sensor in building
    if i < n_cores-1:
        while current_bui_name == last_bui_name:
            last_bui_name = bui_id_df["bui_sh"][pre_list_int]
            pre_list_int += 1
            current_bui_name = bui_id_df["bui_sh"][pre_list_int]
        end_list = pre_list_int

    if i == n_cores-1:
        sen_list = sensor_pts[st_list:]
        dir_list = sensor_dirs[st_list:]
        droplist = droplist_ad[st_list:]
    else:
        sen_list = sensor_pts[st_list:end_list]
        dir_list = sensor_dirs[st_list:end_list]
        droplist = droplist_ad[st_list:end_list]

    droplist_nr = []
    for j in range(0, len(droplist)):
        if droplist[j] == 0:
            droplist_nr.append(int(j))

    for index in sorted(droplist_nr, reverse=True):
        del sen_list[index]
        del dir_list[index]

    droplist_nr = pd.DataFrame(droplist_nr)
    droplist_name = "droplist_nr" + str(i) + ".txt"
    droplist_nr.to_csv(os.path.join(results_path, "temp", droplist_name))
    '''
    arad.set_sensor_points(sensor_pts, sensor_dirs)
    points_file_name = "sensor_points"+str(an_core)+".pts"
    arad.create_sensor_input_file(points_file_name)

    # st_list = end_list

    log((len(sensor_pts), " Sensor points in batch ", an_core), '', awrite_log, aresults_path)
    nr_sen_list.append(len(sensor_pts))
    # write hea file (all information for each run
    arad.execute_gen_dc("w/m2", str(an_core))
    arad.execute_ds_illum()

    '''
    # list of how many sensors are in each batch
    fo = open(os.path.join(aresults_path, "temp", "nr_sen_list.txt"), "w")
    fo.writelines("%s\n" % l for l in nr_sen_list)
    fo.close()


    # seperate calculation for sensor point lists
    clist = []
    for i in range(0, an_cores):
        temp_hea_filepath = os.path.join(aresults_path, 'daysim_data'+str(i)+'\\tmp\\
        daysim_data'+str(i)+"temp"+str(i)+'.hea')
        # command for direct daylight coefficients
        exdir = "gen_dc" + " " + temp_hea_filepath + " " + "-dir"
        # command for diffuse daylight coefficients
        exdif = "gen_dc" + " " + temp_hea_filepath + " " + "-dif"
        # command for ..
        expaste = "gen_dc" + " " + temp_hea_filepath + " " + "-paste"
        # command for writing illumination file
        exillum = "ds_illum" + " " + temp_hea_filepath

        clist.append([exdir, exdif, expaste, exillum])

    process = list(range(0, an_cores))

    for i in range(0, 4):
        for j in range(0, an_cores):
            process[j] = subprocess.Popen(clist[j][i])
        exit_codes = [p.wait() for p in process]
    '''


def create_geometry_lists(an_cores, dimension, geometry_path, list_name, arta):
    geometry_name_list_path = os.path.join(geometry_path, list_name+".csv")
    if not os.path.exists(geometry_name_list_path):
        geometry_name_list = get_list(geometry_path, ".stl")
        geometry_name_list = pd.DataFrame(geometry_name_list)
        geometry_name_list.columns = ['name']
        geometry_name_list.to_csv(geometry_name_list_path, sep=',', index=None)

    geo_list = pd.read_csv(geometry_name_list_path, sep=',')

    if arta is False:
        geo_list = geo_list[geo_list['name'].str.contains("_rta") == False]

    if dimension == "multiple":
        batch_length = geo_list.shape[0]/an_cores
        bui_int = []
        geometry_name_list = []
        geometry_mat_list = []
        bui_int.append(0)
        for n in range(1, an_cores):
            if "_rta" in geo_list['name'][n * batch_length]:
                bui_int.append(n * batch_length+1)
            else:
                bui_int.append(n * batch_length)
        bui_int.append(geo_list.shape[0])

        for n in range(an_cores):
            geometry_name_list.append(geo_list['name'][bui_int[n]:bui_int[n+1]].tolist())
            geometry_mat_list.append(geo_list['mat'][bui_int[n]:bui_int[n+1]].tolist())

    if dimension == "single":
        geometry_name_list = geo_list['name'].tolist()
        geometry_mat_list = geo_list['mat'].tolist()

    return geometry_name_list, geometry_mat_list


def faces2pointlist(filename, abui_name_list, geo_name, faces, atype):
    count = 0
    with open(filename, 'a') as results_file:
        point_list = []

        if geo_name == abui_name_list[0]:
            global nr_faces
            nr_faces = 0
        face_list_up = []
        normal_list_up = []

        for f in faces:


            count += 1
            normal = face_normal(f, nr_faces)

            if atype != "building":
                normal = (1, 1, 1)

            # exclude certain faces
            if not normal[2] > 3:

                pnt_coord = []
                wire_list = Topology.Topo(f).wires()
                for wire in wire_list:
                    edges_list = Topology.Topo(wire).edges()
                    for edge in edges_list:
                        vertice_list = Topology.Topo(edge).vertices()
                        for vertex in vertice_list:
                            pnt_coord.append(
                                [geo_name, int(nr_faces), BRep.BRep_Tool().Pnt(vertex).X(),
                                 BRep.BRep_Tool().Pnt(vertex).Y(), BRep.BRep_Tool().Pnt(vertex).Z(), normal[0],
                                 normal[1], normal[2]])
                pnt_coord = make_unique(pnt_coord)
                for point in pnt_coord:
                    point_list.append(point)

                face_list_up.append(f)
                normal_list_up.append(normal)

                nr_faces += 1
        point_list = pd.DataFrame(point_list)

        '''
        if "rta" in geo_name:
            for j in range(len(face_list_up)):
                normal_list_up[j] = tuple(np.array(normal_list_up[j]) * -1)
                log((geo_name, "face ", j,"reversed"), '', write_log, results_path)
        '''


        if atype == "building" and "rta" not in geo_name:
            bui_centroid = np.array(point_list[[2,3,4]].mean().tolist())
            for j in range(len(face_list_up)):

                fac_centroid = np.array(py3dmodel.calculate.face_midpt(face_list_up[j]))
                fac_vec = np.array(normal_list_up[j])
                vec = bui_centroid-fac_centroid
                angle = np.arccos(np.dot(fac_vec,vec)/(np.linalg.norm(vec)*np.linalg.norm(fac_vec)))*180/np.pi
                if angle < 90:
                    normal_list_up[j] = tuple(np.array(normal_list_up[j])*-1)
                    #print geo_name, "reversed face", j, normal_list_up[j]
                    log((geo_name, "face ", j, "reversed"), '', write_log, results_path)


        # calculate angle
        point_list.to_csv(results_file, float_format='%10.2f', header=None, index=None)

    return face_list_up, normal_list_up


def import_stl(an_core, geo_name_list, geo_path, atype):

    filename = os.path.join(results_path, "temp", atype + "_points_" + str(an_core) + ".csv")
    if os.path.exists(filename):
        os.remove(filename)

    geo_list = []

    face_list = [0]*len(geo_name_list)
    normal_list = [0]*len(geo_name_list)
    geo_int = 0

    for geo in geo_name_list:
        filepath = os.path.join(geo_path, geo + ".stl")
        geo_solid = TopoDS.TopoDS_Solid()

        StlAPI_Reader().Read(geo_solid, str(filepath))
        geo_list.append(geo_solid)
        if atype == "building":
            props = GProp.GProp_GProps()
            BRepGProp.brepgprop_VolumeProperties(geo_solid, props)

            if props.Mass() < 0 and "rta" not in geo:

                log((geo, "reversed"), '', write_log, results_path)
                geo_solid.Reverse()

            #BRepGProp.brepgprop_VolumeProperties(geo_solid, props)

        # write geometry to results file
        StlAPI_Writer().Write(geo_solid, os.path.join(results_path, "temp", "geometry", geo + '.stl'), False)
        # extract faces from solid
        face_list[geo_int] = py3dmodel.fetch.faces_frm_solid(geo_solid)
        # save faces to csv
        face_list[geo_int], normal_list[geo_int] = faces2pointlist(filename, geo_name_list, geo, face_list[geo_int], atype)
        geo_int += 1

    return geo_list, face_list, normal_list


# ========================================================================= #
# main script
# ========================================================================= #

if __name__ == '__main__':
#def execute(resolution, ov_n_cores, ov_write_log):
    # =============================== parameters =============================== #
    time0 = time.clock()
    global write_log
    global results_path
    username = 'lensa'
    # file locations
    current_path = os.path.dirname(__file__)
    input_path = 'C:\\Users\\' + username + '\\polybox\\Master_IBS\\04_semester\\masterthesis\\02_Simulation\\' \
                                            '01_testcase\\cea-reference-case\\reference-case\\baseline\\1-inputs'


    execute = pd.read_csv(os.path.join(input_path, "execute.csv"))
    header = execute["params"].values.tolist()

    for run_index in range(execute.shape[1]-1):
        data = execute["run" + str(run_index)].values.tolist()
        params = pd.DataFrame(data).T
        params.columns = header

        if params["write_log"].values == 'False':
            write_log = False
        else:
            write_log = True
        if params["rta"].values == 'False':
            rta = False
        else:
            rta = True

        project_name = params["project_name"].get_value(0)
        geometry_folder = params["geometry_folder"].get_value(0)
        building_list_name = params["building_list_name"].get_value(0)
        terrain_folder = params["terrain_folder"].get_value(0)
        terrain_list_name = params["terrain_list_name"].get_value(0)
        geometry_format = params["geometry_format"].get_value(0)

        # Simulation parameters
        n_cores = int(params["n_cores"])
        xdim = int(params["xdim"])
        ydim = int(params["ydim"])
        roof_resolution_increase = float(params["roof_resolution_increase"])
        max_roof_angle = float(params["max_roof_angle"])

        weatherfilepath = os.path.join(input_path, "3-weather\\Zurich.epw")
        latitude = 47.3667
        longtitude = 8.5500
        meridian = 10
        offset = 0.1
        ab = 1
                        # rend. time    (min, fast, acc, max)
        rad_n = float(params["rad_n"])       # Set the ambient accuracy to acc. This value will approximately equal the error from indirect illuminance interpolation. A value of zero implies no interpolation.
        rad_af = params["rad_af"].get_value(0)
        rad_ab = float(params["rad_ab"])      # dir. pr.      (0,0.4.8) the number of ambient bounces to N. This is the maximum number of diffuse bounces computed by the indirect calculation. A value of zero implies no indirect calculation.
        rad_ad = float(params["rad_ad"])   # dir. pr.      (0,32,512,4096) Set the number of ambient divisions to N. The error in the Monte Carlo calculation of indirect illuminance will be inversely proportional to the square root of this number. A value of zero implies no indirect calculation.
        rad_as = float(params["rad_as"])     # dir. pr.      (0,32,256,1024) Set the number of ambient super-samples to N. Super-samples are applied only to the ambient divisions which show a significant change.
        rad_ar = float(params["rad_ar"])    # dir. ovpr.    (8,32,128,0) Set the ambient resolution to res. This number will determine the maximum density of ambient values used in interpolation. Error will start to increase on surfaces spaced closer than the scene size divided by the ambient resolution. The maximum ambient value density is the scene size times the ambient accuracy (see the -aa option below) divided by the ambient resolution. The scene size can be determined using getinfo(1) with the -d option on the input octree.
        rad_aa = float(params["rad_aa"])    # dir. ovpr.    (.5,.2,.15,0) Set the ambient accuracy to acc. This value will approximately equal the error from indirect illuminance interpolation. A value of zero implies no interpolation.
        rad_lr = float(params["rad_lr"])      # min.          (0,4,8,16) Limit reflections to a maximum of N.
        rad_st = float(params["rad_st"])   # min.          (1,.85,.15,0) Set the specular sampling threshold to frac. This is the minimum fraction of reflection or transmission, under which no specular sampling is performed. A value of zero means that highlights will always be sampled by tracing reflected or transmitted rays. A value of one means that specular sampling is never used. Highlights from light sources will always be correct, but reflections from other surfaces will be approximated using an ambient value. A sampling threshold between zero and one offers a compromise between image accuracy and rendering time.
        rad_sj = float(params["rad_sj"])    #               (0,.3,.7,1) Set the specular sampling jitter to frac. This is the degree to which the highlights are sampled for rough specular materials. A value of one means that all highlights will be fully sampled using distributed ray tracing. A value of zero means that no jittering will take place, and all reflections will appear sharp even when they should be diffuse.
        rad_lw = float(params["rad_lw"])  # min.          (.05,.01,.002,0) Limit the weight of each ray to a minimum of frac. During ray-tracing, a record is kept of the final contribution a ray would have to the image. If it is less then the specified minimum, the ray is not traced.
        rad_dj = float(params["rad_dj"])   #               (0,0,.7,1)
        rad_ds = float(params["rad_ds"])    # inv. pr.      (0,0.5,.15,.02) Set the direct sampling ratio to frac. A light source will be subdivided until the width of each sample area divided by the distance to the illuminated point is below this ratio. This assures accuracy in regions close to large area sources at a slight computational expense. A value of zero turns source subdivision off, sending at most one shadow ray to each light source
        rad_dr = float(params["rad_dr"])      # dir. ~pr.     (0,1,3,6) Set the number of relays for secondary sources to N. A value of 0 means that secondary sources will be ignored. A value of 1 means that sources will be made into first generation secondary sources; a value of 2 means that first generation secondary sources will also be made into second generation secondary sources, and so on.
        rad_dp = float(params["rad_dp"])    # min.             (32,64,512,0) Set the secondary source presampling density to D. This is the number of samples per steradian that will be used to determine ahead of time whether or not it is worth following shadow rays through all the reflections and/or transmissions associated with a secondary source path. A value of 0 means that the full secondary source path will always be tested for shadows if it is tested at al

        # override

        # =============================== Preface =============================== #

        results_path = os.path.join(current_path, project_name)
        if os.path.exists(os.path.join(results_path,"log.txt")):
            os.remove(os.path.join(results_path,"log.txt"))

        if not os.path.exists(results_path):
            os.makedirs(results_path)

        temp_path = os.path.join(results_path, "temp")
        if not os.path.exists(temp_path):
            os.makedirs(temp_path)

        if not os.path.exists(os.path.join(temp_path, "geometry")):
            os.makedirs(os.path.join(temp_path, "geometry"))

        bui_name_list = []
        rad = py2radiance.Rad(os.path.join(current_path, 'base.rad'), os.path.join(current_path, 'py2radiance_data'))

        # =============================== Import =============================== #
        # print project_name
        log(("daysim parameters:", rad_n, rad_af, rad_ab, rad_ad, rad_as, rad_ar, rad_aa, rad_lr,
             rad_st, rad_sj, rad_lw, rad_dj, rad_ds, rad_dr, rad_dp), '\n', write_log, results_path)

        time1 = time.clock()
        '''
        if geometry_format == "shp":

            # import terrain
            print "Import terrain"
            terrain_path = os.path.join(input_path, "terrain_polygonised.gml\\terrain_polygonised.shp")
            # should be "DN" elevation index
            terrain_faces = shp2citygml.terrain2d23d_tin(terrain_path, "DN")
            faces2pointlist(os.path.join(results_path, "terrain_points.csv"), ["terrain"],"terrain", terrain_faces)
            terrain_name_list_path = os.path.join(input_path, 'terrain', "terrain_list.csv")
            terrain_list = pd.read_csv(terrain_name_list_path, sep=',')
            terrain_name_list = terrain_list['name'].tolist()
            terrain_mat_list = terrain_list['mat'].tolist()
            print "elapsed time", round((time.clock() - time1) / 60, 1), " min" '\n'


            time1 = time.clock()
            # import buildings list
            db = dbfread.DBF(os.path.join(input_path, 'building\\4buildings.dbf'), load=True)
            for row in range(0, len(db)):
                bui_name_list.append(db.records[row]['Name'])
            bui_name_list_path = os.path.join(input_path, 'building', "bui_list.csv")
            if not os.path.exists(bui_name_list_path):
                bui_name_list = pd.DataFrame(bui_name_list)
                bui_name_list.to_csv(bui_name_list_path, sep=',', index=None)

            bui_list = pd.read_csv(bui_name_list_path, sep=',')
            bui_name_list = bui_list['name'].tolist()
            bui_mat_list = bui_list['mat'].tolist()


            # import buildings
            print "Import buildings"
            building_path = os.path.join(input_path, "building\\4buildings.shp")
            building_solids = shp2citygml.building2d23d(building_path, "height_ag", terrain_faces)
            bui_int = 0
            for building_solid in building_solids:
                bui_faces = py3dmodel.fetch.faces_frm_solid(building_solid)
                print str(bui_name_list[bui_int])
                faces2pointlist(os.path.join(results_path, "bui_points.csv"),bui_name_list, str(bui_name_list[bui_int]),
                bui_faces)
                StlAPI_Writer().Write(building_solid, os.path.join(temp_path, "geometry",
                                                                   str(bui_name_list[bui_int])+'.stl'), False)

                bui_int += 1
            print "elapsed time", round((time.clock() - time1) / 60, 1), " min" '\n'
        '''

        if geometry_format == "stl":
            # import terrain
            time1 = time.clock()
            log("Import terrain", '', write_log, results_path)
            terrain_name_list, terrain_mat_list = create_geometry_lists(n_cores, "single",
                                                                        os.path.join(input_path, terrain_folder),
                                                                        terrain_list_name, rta)
            terrain_solids, terrain_faces, dummy_normal = import_stl(0, terrain_name_list, os.path.join(input_path, terrain_folder),
                                                       "terrain")
            log(("elapsed time", round((time.clock() - time1) / 60, 1), " min"), '\n', write_log, results_path)

            # import buildings
            time1 = time.clock()
            log("Import buildings", '', write_log, results_path)
            bui_name_list, bui_mat_list = create_geometry_lists(n_cores, "multiple",
                                                                os.path.join(input_path, geometry_folder),
                                                                building_list_name, rta)

            face_lists = [0] * n_cores
            normal_lists = [0] * n_cores
            buildingsolids_lists = [0] * n_cores

            for n_core in range(n_cores):
                buildingsolids_lists[n_core], face_lists[n_core], normal_lists[n_core] = import_stl(n_core, bui_name_list[n_core],
                                                                              os.path.join(input_path, geometry_folder),
                                                                              "building")

            log(("elapsed time", round((time.clock() - time1) / 60, 1), " min"), '\n', write_log, results_path)

        # Export building geomery
        # print 'Export STL geometry \n'
        # export_stl()

        # =============================== Simulation =============================== #
        time1 = time.clock()
        # Geometry to radiance
        log('Transfer geometry to radiance', '', write_log, results_path)
        geometry2radiance(rad, buildingsolids_lists, bui_mat_list)

        # Terrain into radiance
        log('Transfer terrain to radiance \n', '', write_log, results_path)
        terrain2radiance(rad, terrain_solids, terrain_faces, terrain_mat_list, terrain_name_list)

        # calculate sensor points
        log('Calculate sensor points', '', write_log, results_path)

        multiprocess(generate_sensor_points, ("dummy_n_core", results_path, write_log, bui_name_list, face_lists, normal_lists, xdim, ydim,
                                              offset, roof_resolution_increase, max_roof_angle), n_cores)

        rad.create_rad_input_file()


        # calculate radiance for one hour --> evaluate adjacency
        # print '\nEvaluate adjacency'
        # droplist_ad = calc_adjacency((rad, sensor_pts, sensor_dirs, weatherfilepath, ab))

        droplist_ad = []

        # Execute daysim
        log("\nDaysim evaluation",'', write_log, results_path)
        multiprocess(execute_daysim, ("dummy_n_core", results_path, write_log, rad, weatherfilepath, rad_n, rad_af, rad_ab,
        rad_ad, rad_as, rad_ar, rad_aa, rad_lr, rad_st, rad_sj, rad_lw, rad_dj, rad_ds, rad_dr, rad_dp), n_cores)
        log(("elapsed time", round((time.clock() - time1) / 60, 1), " min"), '\n', write_log, results_path)

        # =============================== Rework =============================== #

        time1 = time.clock()

        spatial_time_average_list = ["day", "month", "year"]
        # spatial_time_average_list = ["year"]
        spatial_average_list = ["sen", "bui", "bui_fac"]

        zone_time_average_list = ["hour"]  # , "day", "month", "year"]
        # zone_averge_list = ["sen_sg", "sen_sp", "bui_sg", "bui_sp", "bui_dir", "bui_zone"]
        zone_averge_list = ["bui_sp", "bui_sg"]



        chunk_size = 10000

        ''''''
        # bui_zone_roof_average(1, n_cores, results_path, zone_averge_list, zone_time_average_list[0])
        # bui_zone_roof_average(3, n_cores, results_path, zone_averge_list, zone_time_average_list[0])
        # sen_average(0, n_cores, results_path, spatial_average_list[2],  spatial_time_average_list[0])
        # concat_results(n_cores, results_path, spatial_average_list[1], time_average_list[3], chunk_size)
        ''''''
        # =============================== time averaging =============================== #
        time1 = time.clock()
        processes = []
        for i in range(n_cores):
            process = Process(target=time_sums, args=(i, results_path, spatial_time_average_list))
            process.start()
            processes.append(process)
        for process in processes:
            process.join()
        print "\n----------------- time averaging", round((time.clock() - time1) / 60, 1), "min -----------------\n"

        # =============================== spatial averaging =============================== #
        time1 = time.clock()
        processes = []
        for i in range(n_cores):
            for sp in range(0, len(spatial_average_list)):
                for t in range(0, len(spatial_time_average_list)):
                    process = Process(target=sen_average, args=(i, n_cores, results_path, spatial_average_list[sp],
                                                                spatial_time_average_list[t]))
                    process.start()
                    processes.append(process)
        for process in processes:
            process.join()
        print "\n----------------- spatial averaging", round((time.clock() - time1) / 60, 1), "min -----------------\n"

        # =============================== zone/roof averaging =============================== #
        time1 = time.clock()
        processes = []
        for i in range(n_cores):
            for t in range(0, len(zone_time_average_list)):
                process = Process(target=bui_zone_roof_average, args=(i, n_cores, results_path, zone_averge_list,
                                                                      zone_time_average_list[t], chunk_size))
                process.start()
                processes.append(process)
        for process in processes:
            process.join()
        print "\n----------------- zone/roof averaging", round((time.clock() - time1) / 60,
                                                               1), "min -----------------\n"

        # =============================== coacentate =============================== #
        time1 = time.clock()
        processes = []

        for t in range(0, len(spatial_time_average_list)):
            for sp in range(0, len(spatial_average_list)):
                process = Process(target=concat_results, args=(n_cores, results_path, spatial_average_list[sp],
                                                               spatial_time_average_list[t], chunk_size))
                process.start()
                processes.append(process)
        for process in processes:
            process.join()

        for t in range(0, len(zone_time_average_list)):
            for zo in range(0, len(zone_averge_list)):
                process = Process(target=concat_results, args=(n_cores, results_path, zone_averge_list[zo],
                                                               zone_time_average_list[t], chunk_size))
                process.start()
                processes.append(process)
        for process in processes:
            process.join()

        concat_results(n_cores, results_path, "bui_id", "df", chunk_size)

        print "\n----------------- coacentaing", round((time.clock() - time1) / 60, 1), "min -----------------\n"





        # print "averaging"
        # from averaging import run_averaging
        # run_averaging(n_cores, results_path)
        # print "elapsed time", round((time.clock()-time1)/60, 1), " min" '\n'

        log(("total time", round((time.clock()-time0)/60, 1), " min"), '\n', write_log, results_path)


        #