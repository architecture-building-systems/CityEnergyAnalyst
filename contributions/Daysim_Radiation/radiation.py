import os
import time
import numpy as np
import pandas as pd
import math
import shutil
from multiprocessing import Process

from OCC import BRepGProp, GProp, BRep, TopoDS
from OCC.StlAPI import StlAPI_Reader, StlAPI_Writer
from OCC.TopAbs import TopAbs_REVERSED
from OCCUtils import face, Topology

import shp2citygml
import gml3dmodel
import interface2py3d
import py3dmodel
from py3dmodel import py2radiance




def face_normal(occface):
    fc = face.Face(occface)
    centre_uv, centre_pt = fc.mid_point()
    normal_dir = fc.DiffGeom.normal(centre_uv[0], centre_uv[1])
    if occface.Orientation() == TopAbs_REVERSED:
        normal_dir = normal_dir.Reversed()
    normal = (normal_dir.X(), normal_dir.Y(), normal_dir.Z())
    return normal


def add_rad_mat(aresults_path, an_core, names, values):
    file_path = os.path.join(aresults_path, 'daysim_data' + str(an_core) + '\\rad\\daysim_data' + str(an_core) +
                             "_material")
    file_name_rad = file_path + ".rad"
    file_name_txt = file_path + ".txt"
    os.rename(file_name_rad, file_name_rad.replace(".rad", ".txt"))
    with open(file_name_txt, 'a') as write_file:
        name_int = 0
        for name in names:
            value = values[name_int]
            string = "void plastic " + name + " 0 0 5 " + str(value) + " " + str(value) + " " + str(value) \
                     + " 0.0000 0.0000"
            write_file.writelines('\n' + string + '\n')
            name_int += 1
        write_file.close()
    os.rename(file_name_txt, file_name_rad.replace(".txt", ".rad"))


def percentage(task, now, total):
    percent = round((float(now)/float(total))*100, 0)
    division = 5
    number = int(round(percent/division, 0))

    bar = number * ">" + (100 / division - number) * "_"
    if now == total:
        print "\r", str(task), bar, percent, "%",
    else:
        print "\r", str(task),bar, percent, "%",


def bui_id_df_per_building_one(an_core, aresults_path):
    abui_id_df = pd.read_csv(os.path.join(aresults_path, "temp", 'bui_id_df_' + str(an_core) + '.csv'))
    bui_list = abui_id_df['bui'].values.tolist()
    bui_list = list(set(bui_list))
    for bui in bui_list:
        #abui_id_df[abui_id_df['bui'] == bui].to_csv(os.path.join(aresults_path, 'buildings', bui+'_id_df.csv'), index=None)
        one_bui_id_df = abui_id_df[abui_id_df['bui'] == bui]
        one_bui_id_df.reset_index(drop=True)
        keep = 2
        drop_list = range(one_bui_id_df.shape[0])
        for inter in range(one_bui_id_df.shape[0] - 1, -1, -keep):
            del drop_list[inter]
        one_bui_id_df.drop(one_bui_id_df.index[drop_list], axis=0, inplace=True)
        one_bui_id_df['sen_area'] = one_bui_id_df['sen_area'] * 2
        one_bui_id_df.to_csv(os.path.join(aresults_path, 'buildings', bui + '_id_df.csv'), index=None)



def bui_id_df_per_building(an_core, aresults_path):
    abui_id_df = pd.read_csv(os.path.join(aresults_path, "temp", 'bui_id_df_' + str(an_core) + '.csv'))
    bui_list = abui_id_df['bui'].values.tolist()
    bui_list = list(set(bui_list))
    for bui in bui_list:
        #abui_id_df[abui_id_df['bui'] == bui].to_csv(os.path.join(aresults_path, 'buildings', bui+'_id_df.csv'), index=None)
        one_bui_id_df = abui_id_df[abui_id_df['bui'] == bui]
        one_bui_id_df.reset_index(drop=True)
        split = 4.0
        delta = (one_bui_id_df.shape[0]-1) / split

        for row_chunk in range(int(split)):
            row_start = int(row_chunk * delta)
            row_end = int((row_chunk + 1) * delta)
            one_bui_id_df_chunk = one_bui_id_df[row_start:row_end]
            keep = 2
            drop_list = range(one_bui_id_df_chunk.shape[0])
            for inter in range(one_bui_id_df_chunk.shape[0] - 1, -1, -keep):
                del drop_list[inter]
            one_bui_id_df_chunk.drop(one_bui_id_df_chunk.index[drop_list], axis=0, inplace=True)
            one_bui_id_df_chunk['sen_area']=one_bui_id_df_chunk['sen_area']*2
            one_bui_id_df_chunk.to_csv(os.path.join(aresults_path, 'buildings', bui + '_' + str(row_chunk) + '_id_df.csv'),
                                       index=None)



def hourly_file_per_building_one(an_core, an_cores, aresults_path, achunk_size_bui):
    # get sensors per building
    sen_interval, face_area, aheader, bool_dummy, sen_area = \
        sensors_per_building_face_area1(an_core, an_cores, aresults_path, "bui")
    # get sensor id file
    abui_id_df = pd.read_csv(os.path.join(aresults_path, "temp", 'bui_id_df_' + str(an_core) + '.csv'))
    # get data file
    data_file = os.path.join(aresults_path, "temp", "sen_hour_" + str(an_core) + ".csv")
    # sensor = pd.read_csv(sensor_file, sep=',', aheader=None).T
    for bui in range(len(sen_interval) - 1):
        # progress bar
        percentage("save building sensor files " + str(an_core), bui + 1, len(sen_interval) - 1)
        # make aheader
        aheader = abui_id_df.ix[sen_interval[bui]:sen_interval[bui + 1] - 1, 5:6].T
        # parameters
        bui_name = abui_id_df["bui"][sen_interval[bui]]
        results_file_path = os.path.join(aresults_path, "buildings", bui_name + ".csv")
        if os.path.exists(results_file_path):
            os.remove(results_file_path)
        results_file = open(results_file_path, 'ab')
        aheader.to_csv(results_file, sep=',', header=None, index=None)
        lines = True
        iterator = 0
        while lines is True:
            # data chunk
            adata = pd.read_csv(data_file, sep=',', header=None, skiprows=iterator * achunk_size_bui,
                                nrows=achunk_size_bui)
            if adata.shape[0] != achunk_size_bui:
                lines = False
            # building chunk
            chunk = adata.ix[:,sen_interval[bui]:sen_interval[bui + 1]]
            keep = 2
            drop_list = range(chunk.shape[1])
            for inter in range(chunk.shape[1] - 1, -1, -keep):
                del drop_list[inter]
            chunk.drop(chunk.columns[drop_list], axis=1, inplace=True)

            chunk.to_csv(results_file, sep=',', header=None, index=None)
            # aheader = pd.concat([aheader, chunk], axis=0)
            iterator += 1
        results_file.close()


def hourly_file_per_building(an_core, an_cores, aresults_path, achunk_size_bui):
    # get sensors per building
    sen_interval, face_area, aheader, bool_dummy, sen_area = sensors_per_building_face_area1(an_core, an_cores, aresults_path,
                                                                                   "bui")
    # get sensor id file
    abui_id_df = pd.read_csv(os.path.join(aresults_path, "temp", 'bui_id_df_' + str(an_core) + '.csv'))
    # get data file
    data_file = os.path.join(aresults_path, "temp", "sen_hour_" + str(an_core) + ".csv")
    # sensor = pd.read_csv(sensor_file, sep=',', aheader=None).T
    for bui in range(len(sen_interval)-1):
        # progress bar
        percentage("save building sensor files "+str(an_core), bui+1, len(sen_interval)-1)
        # make aheader
        aheader = abui_id_df.ix[sen_interval[bui]:sen_interval[bui+1]-1, 5:6].T

        # parameters
        bui_name = abui_id_df["bui"][sen_interval[bui]]
        split = 4.0
        results_files = {}
        for col_chunk in range(int(split)):
            results_file_path = os.path.join(aresults_path, "buildings", bui_name + '_'+str(int(col_chunk))+".csv")
            if os.path.exists(results_file_path):
                os.remove(results_file_path)
            results_files[col_chunk] = open(results_file_path, 'ab')
            aheader = pd.read_csv(os.path.join(aresults_path, 'buildings', bui_name + '_' + str(col_chunk) + '_id_df.csv'))

            aheader = aheader.ix[:, 5:6].T

            aheader.to_csv(results_files[col_chunk], sep=',', header=None, index=None)


        lines = True
        iterator = 0
        while lines is True:
            # data chunk
            adata = pd.read_csv(data_file, sep=',', header=None, skiprows=iterator * achunk_size_bui,
                                nrows=achunk_size_bui)
            if adata.shape[0] != achunk_size_bui:
                lines = False
            # building chunk
            # split file into 4 pieces

            start = sen_interval[bui]
            end = sen_interval[bui + 1] - 1
            delta = (end - start)/split


            for col_chunk in range(int(split)):
                col_start = int(col_chunk*delta + start)
                col_end = int((col_chunk+1)*delta + start)-1
                
                chunk = adata.ix[:, col_start:col_end]


                keep = 2
                drop_list = range(chunk.shape[1])
                for inter in range(chunk.shape[1] - 1, -1, -keep):
                    del drop_list[inter]
                chunk.drop(chunk.columns[drop_list], axis=1, inplace=True)
                ''''''

                chunk.to_csv(results_files[col_chunk], sep=',', header=None, index=None)
            #aheader = pd.concat([aheader, chunk], axis=0)
            iterator += 1

        for col_chunk in range(int(split)):
            results_files[col_chunk].close()



def sensors_per_building_face_area1(an_core, an_cores, aresults_path, acol_key):
    abui_id_df = pd.read_csv(os.path.join(aresults_path, "temp", 'bui_id_df_' + str(an_core) + '.csv'))
    abui_id_df_batch = abui_id_df[acol_key].values.tolist()
    face_area = abui_id_df["fac_area"].values.tolist()
    sen_area = abui_id_df["sen_area"].values.tolist()
    sen_interval = []
    header = []
    previous_name = abui_id_df_batch[0]
    # insert the starting integer
    sen_interval.append(0)
    header.append(abui_id_df_batch[0])
    for j in range(0, len(abui_id_df_batch)):
        actual_name = abui_id_df_batch[j]
        if actual_name != previous_name:
            sen_interval.append(j)
            header.append(abui_id_df_batch[j])
        previous_name = actual_name
    # insert last integer in batch
    sen_interval.append(j+1)
    # add boolean vector for facade and roof (decide on angle)
    alist = abui_id_df['tilt'].values.tolist()
    bool_facade = [1 if x >= 89 else 0 for x in alist]

    return sen_interval, face_area, header, bool_facade, sen_area


def concat_results(atime_sum, aspatial_sum, an_cores, aresults_path, achunk_size, awrite_log):
    with open(os.path.join(aresults_path, aspatial_sum + "_" + atime_sum + ".csv"), 'w') as results_file:
        lines = True
        iterator = 0
        while lines is True:
            for j in range(an_cores):
                adata = pd.read_csv(os.path.join(aresults_path, "temp", aspatial_sum + "_" + atime_sum + "_" + str(j) +
                                                 ".csv"), sep=',', header=None, skiprows=iterator * achunk_size,
                                    nrows=achunk_size)
                if adata.shape[0] != achunk_size:
                    lines = False
                if j == 0:
                    result = adata
                else:
                    result = pd.concat([result, adata], axis=1)
            result.to_csv(results_file, sep=',', header=None, index=None)
            iterator += 1
    log(("coacenated", result.shape[1], aspatial_sum, "for", atime_sum), '', awrite_log, aresults_path)
    results_file.close()


def time_sums(an_core, aresults_path):
    illum_file_path = os.path.join(aresults_path, 'daysim_data' + str(an_core), 'res', 'daysim_data' + str(an_core))
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
                if day_sum.shape != sensor_series.shape:
                    print(hourinyear, day_sum.shape , sensor_series.shape)
                day_sum = np.sum([day_sum, sensor_series], axis=0)
                if hourinyear % 24 == 0:
                    day = int(np.ceil(hourinyear/24))
                    days = np.append(days, day_sum, axis=0)
                    day_sum = day_sum_0
                    percentage("time sums "+str(an_core), day, daysinyear)
            hourinyear += 1
    days = days.reshape((daysinyear, sens_nr))
    ins.close()
    sen_hour.close()
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
    np.savetxt(os.path.join(aresults_path, "temp", "sen_month_" + str(an_core)+".csv"), months, fmt='%1.1f',
               delimiter=",")


def sen_average(an_core, atime_sum, aspatial_sum, an_cores, aresults_path, awrite_log):
    if aspatial_sum == "sen":
        return
    sen_interval, face_area, header, bool_facade, sen_area = sensors_per_building_face_area1(an_core, an_cores, aresults_path,
                                                                                   aspatial_sum)
    bool_facade = np.array(bool_facade)

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

    res_vert = np.zeros((time_steps, len(sen_interval)-1))
    res_tot = np.zeros((time_steps, len(sen_interval) - 1))
    res_rel = np.zeros((time_steps, len(sen_interval) - 1))

    with open(sensor_file, "r") as ins:
        hourinyear = 0
        # loop all hours of a file (hour, day, month, year)
        for line in ins:
            sensor_series = line.split(sep)
            if atime_sum == "hour":
                sensor_series = [float(j) for j in sensor_series[4:]]
            else:
                sensor_series = [float(j) for j in sensor_series]

            sensor_series = np.array(sensor_series)

            # loop over buildings in each batch
            for k in range(0, len(sen_interval)-1):

                # mean of W/m2 per sensor times m2 per face --> average kW per face
                res_vert[hourinyear, k] = np.sum(sensor_series[sen_interval[k]:sen_interval[k + 1]] *
                                                 bool_facade[sen_interval[k]:sen_interval[k + 1]] *
                                                 sen_area[sen_interval[k]:sen_interval[k + 1]])
                res_tot[hourinyear, k] = np.mean(sensor_series[sen_interval[k]:sen_interval[k + 1]] *
                                                 face_area[sen_interval[k]:sen_interval[k + 1]])
                res_rel[hourinyear, k] = np.mean(sensor_series[sen_interval[k]:sen_interval[k + 1]])


            hourinyear += 1
    ins.close()
    res_vert = pd.DataFrame(res_vert)
    res_tot = pd.DataFrame(res_tot)
    res_rel = pd.DataFrame(res_rel)

    res_vert.to_csv(os.path.join(aresults_path, "temp", aspatial_sum+"_"+atime_sum + "_" + str(an_core) + ".csv"),
                   header=None, index=False, float_format='%1.1f')
    res_tot.to_csv(os.path.join(aresults_path, "temp", aspatial_sum + "_tot_" + atime_sum + "_" + str(an_core) + ".csv"),
                   header=None, index=False, float_format='%1.1f')

    res_rel.to_csv(os.path.join(aresults_path, "temp", aspatial_sum + "_rel_" + atime_sum + "_" + str(an_core) + ".csv"),
                   header=None, index=False, float_format='%1.1f')


    log(("batch ", an_core, len(sen_interval) - 1, aspatial_sum, atime_sum), '', awrite_log, aresults_path)


def log(message, wordwrap, awrite_log, aresults_path):

    file_name = "log.txt"
    message = str(message).replace("'", "").replace('(', '').replace(')', '').replace(',', '')

    if awrite_log is True:
        with open(os.path.join(aresults_path, file_name), 'ab') as log_file:
            log_file.write('\n'+message+wordwrap)
            log_file.close()

    print message, wordwrap


def multiprocess(nr_lists, function, arguments, lists):
    # TODO delete nr_lists
    processes = []
    if len(lists) == 1:
        for item0 in lists[0]:
            argument_list = list(arguments)
            argument_list[0] = item0
            arguments = tuple(argument_list)
            process = Process(target=function, args=arguments)
            process.start()
            processes.append(process)

    if len(lists) == 2:
        for item0 in lists[0]:
            for item1 in lists[1]:
                argument_list = list(arguments)
                argument_list[0] = item0
                argument_list[1] = item1
                arguments = tuple(argument_list)
                process = Process(target=function, args=arguments)
                process.start()
                processes.append(process)

    if len(lists) == 3:
        for item0 in lists[0]:
            for item1 in lists[1]:
                for item2 in lists[2]:
                    argument_list = list(arguments)
                    argument_list[0] = item0
                    argument_list[1] = item1
                    argument_list[2] = item2
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
    abui_id_df = []

    # loop over all builings
    bcnt = 0
    for bui_name in abui_name_list:
        bui_sen_nr = []
        if bui_name.find("_") == -1:
            name_length = len(bui_name)
        else:
            name_length = bui_name.find("_")
        bui_name_short = bui_name[0:name_length]
        bui_face_list = face_list[bcnt]
        bui_normal_list = normal_list[bcnt]
        # loop thru the faces in the solid
        fac_int = 0
        for f in bui_face_list:
            normal = bui_normal_list[fac_int]
            # increase resolution on roof tops
            if normal[2] >= amax_roof_angle:
                axdim = axdim/aroof_resolution_increase
                aydim = aydim/aroof_resolution_increase
            else:
                axdim = axdim
                aydim = aydim
            # generate sensor points for a surface, create sensor points,surfaces with divions of xdim and ydim of
            # the domain of f
            a_sensor_srfs, a_sensor_pts, a_sensor_dirs = gml3dmodel.generate_sensor_surfaces(f, axdim, aydim, aoffset,
                                                                                             normal)
            fac_area = py3dmodel.calculate.face_area(f)
            # generate dataframe with building, face and sensor ID
            sen_int = 0
            for sen_dir in a_sensor_dirs:
                orientation = math.copysign(math.acos(normal[1]),normal[0])*180/math.pi
                tilt = math.acos(normal[2])*180/math.pi
                abui_id_df.append((bui_name, bui_name_short, fac_int, str(bui_name)+'_'+str(fac_int), sen_int,
                                  str(bui_name)+'_'+str(fac_int)+'_'+str(sen_int), fac_area,
                                  fac_area/len(a_sensor_dirs), a_sensor_pts[sen_int][0], a_sensor_pts[sen_int][1],
                                  a_sensor_pts[sen_int][2], normal[0], normal[1], normal[2], orientation, tilt))
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

        total_faces = total_faces + fac_int
        total_sensors = total_sensors + sum(bui_sen_nr)
    log("----------------------------------------------", '', awrite_log, aresults_path)
    log(("batch", an_core, "total:", bcnt, "buildings", total_faces, "faces", total_sensors, "sensors"), "\n",
        awrite_log, aresults_path)
    abui_id_df = pd.DataFrame(abui_id_df,
                              columns=['bui', 'bui_sh', 'fac', 'bui_fac', 'sen_int', 'bui_fac_sen', 'fac_area',
                                       'sen_area', 'sen_x', 'sen_y',
                                       'sen_z', 'sen_dir_x', 'sen_dir_y', 'sen_dir_z', 'orientation', 'tilt'])
    abui_id_df.to_csv(os.path.join(aresults_path, "temp", 'bui_id_df_'+str(an_core)+'.csv'), index=None)


def execute_daysim(an_core, aresults_path, awrite_log, arad, aweatherfilepath, arad_n, arad_af, arad_ab, arad_ad,
                   arad_as, arad_ar, arad_aa, arad_lr, arad_st, arad_sj, arad_lw, arad_dj, arad_ds, arad_dr, arad_dp,
                   amat_name_list, amat_value_list):
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

    add_rad_mat(aresults_path, an_core, amat_name_list, amat_value_list)

    # set simulation parameters the default settings are the complex scene 1 settings of daysimPS
    # rad.write_default_radiance_parameters()
    arad.write_radiance_parameters(arad_n, arad_af, arad_ab, arad_ad, arad_as, arad_ar, arad_aa, arad_lr, arad_st,
                                   arad_sj, arad_lw, arad_dj, arad_ds, arad_dr, arad_dp)

    arad.set_sensor_points(sensor_pts, sensor_dirs)
    points_file_name = "sensor_points"+str(an_core)+".pts"
    arad.create_sensor_input_file(points_file_name)

    # st_list = end_list

    log((len(sensor_pts), " Sensor points in batch ", an_core), '', awrite_log, aresults_path)
    nr_sen_list.append(len(sensor_pts))
    # write hea file (all information for each run
    arad.execute_gen_dc("w/m2", str(an_core))
    arad.execute_ds_illum()

    # rename illumination file
    illum_file_path = os.path.join(aresults_path, 'daysim_data' + str(an_core), 'res', 'daysim_data' + str(an_core))
    filename = illum_file_path + '.ill'
    base_file, ext = os.path.splitext(filename)
    os.rename(filename, base_file + ".txt")


def create_geometry_lists(an_cores, dimension, geometry_path, list_name, arta, geometry_name_list_ranges):
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

        if geometry_name_list_ranges == None:
            for an_core in range(an_cores):
                geometry_name_list.append(geo_list['name'][bui_int[an_core]:bui_int[an_core+1]].tolist())
                geometry_mat_list.append(geo_list['mat'][bui_int[an_core]:bui_int[an_core+1]].tolist())
        else:
            for an_core in range(an_cores):
                geometry_name_list.append(geo_list['name'][geometry_name_list_ranges[an_core]:
                geometry_name_list_ranges[an_core+1]].tolist())
                geometry_mat_list.append(geo_list['mat'][geometry_name_list_ranges[an_core]:
                geometry_name_list_ranges[an_core+1]].tolist())

    if dimension == "single":
        geometry_name_list = geo_list['name'].tolist()
        geometry_mat_list = geo_list['mat'].tolist()

    return geometry_name_list, geometry_mat_list


def faces2pointlist(filename, abui_name_list, geo_name, faces, atype):

    with open(filename, 'a') as results_file:
        point_list = []
        cen_point_list = []


        # reset face integer for first building in building batch name list
        if abui_name_list[0] == geo_name:
            global nr_faces
            nr_faces = 0

        face_list_up = []
        normal_list_up = []

        # First loop: calculate all points of each face and retrieve the building_centroid
        for f in faces:
            normal = face_normal(f)
            face_list_up.append(f)
            normal_list_up.append(normal)

            if atype == "building":
                # calculate points of faces for
                pnt_coord = []
                wire_list = Topology.Topo(f).wires()
                for wire in wire_list:
                    edges_list = Topology.Topo(wire).edges()
                    for edge in edges_list:
                        vertice_list = Topology.Topo(edge).vertices()
                        for vertex in vertice_list:
                            pnt_coord.append([BRep.BRep_Tool().Pnt(vertex).X(), BRep.BRep_Tool().Pnt(vertex).Y(),
                                              BRep.BRep_Tool().Pnt(vertex).Z()])
                pnt_coord = make_unique(pnt_coord)
                for point in pnt_coord:
                    cen_point_list.append(point)
                cen_point_list = pd.DataFrame(cen_point_list)
                bui_centroid = np.array(cen_point_list[[0, 1, 2]].mean().tolist())

        # Second loop: calculate scalar product of face vector and vector from building centroid to face center, if the
        #  angle smaller than 90 degrees the face is reversed
        if atype == "building":
            for j in range(len(face_list_up)):
                fac_centroid = np.array(py3dmodel.calculate.face_midpt(face_list_up[j]))
                fac_vec = np.array(normal_list_up[j])
                vec = bui_centroid - fac_centroid
                angle = np.arccos(np.dot(fac_vec, vec) / (np.linalg.norm(vec) * np.linalg.norm(fac_vec))) * 180 / np.pi
                if angle < 90:
                    normal_list_up[j] = tuple(np.array(normal_list_up[j]) * -1)
                    # print geo_name, "reversed face", j, normal_list_up[j]
                    #log((geo_name, "face ", j, "reversed"), '', write_log, results_path)

        # Thrid loop: exclude faces pointing downwards
        if atype == "building":
            for i in range(len(face_list_up) - 1, -1, -1):
                if normal_list_up[i][2] < -0.85:
                    #log((geo_name, "face ", i, "removed"), '', write_log, results_path)
                    normal_list_up.pop(i)
                    face_list_up.pop(i)

        # Fourth loop: calculate building points from faces which are not excluded
        fac_int = 0
        for f in face_list_up:
            normal = normal_list_up[fac_int]
            if atype != "building":
                normal = (1, 1, 1)
            # calculate face points
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
            fac_int += 1
            nr_faces += 1
        point_list = pd.DataFrame(point_list)
        point_list.to_csv(results_file, float_format='%10.2f', header=None, index=None)
    results_file.close()
    return face_list_up, normal_list_up


def import_stl(an_core, geo_name_list, geo_path, atype):

    filename = os.path.join(results_path, "temp", atype + "_points_" + str(an_core) + ".csv")
    if os.path.exists(filename):
        os.remove(filename)

    geo_list = []
    bui_vol = []
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
                bui_vol.append(-props.Mass())
                #log((geo, "reversed"), '', write_log, results_path)
                geo_solid.Reverse()
            else:
                bui_vol.append(props.Mass())

            #BRepGProp.brepgprop_VolumeProperties(geo_solid, props)

        # write geometry to results file
        StlAPI_Writer().Write(geo_solid, os.path.join(results_path, "temp", "geometry", geo + '.stl'), False)

        # extract faces from solid
        face_list[geo_int] = py3dmodel.fetch.faces_frm_solid(geo_solid)
        # save faces to csv
        face_list[geo_int], normal_list[geo_int] = faces2pointlist(filename, geo_name_list, geo, face_list[geo_int], atype)
        geo_int += 1

    return geo_list, face_list, normal_list, bui_vol



def mod_rad_params(params, rad_param_name, rad_param_value):

    previous_value = params[rad_param_name][0]

    params[rad_param_name] = rad_param_value
    log(('changed', rad_param_name, 'from', previous_value, 'to', rad_param_value), '\n', write_log, results_path)
    return params


# ========================================================================= #
# main script
# ========================================================================= #

#if __name__ == '__main__':
def calc_radiation(scenario_path, case, scenario_name, params_mod):
    # =============================== parameters =============================== #
    time0 = time.clock()
    global write_log
    global results_path

    #nr_runs = 50
    #scenario_path = 'C:/reference-case_HQ'

    cea_path = 'C:\Users\Assistenz\Documents\GitHub\CEAforArcGIS\cea'
    current_path = os.path.dirname(__file__)

    # input path
    input_path = os.path.join(scenario_path, case, scenario_name, 'inputs')
    # results path
    results_path = os.path.join(scenario_path, case, scenario_name, 'outputs', 'data', 'solar-radiation')

    execute = pd.read_csv(os.path.join(scenario_path, case, "execute.csv"))

    header = execute["params"].values.tolist()
    #data = execute["run" + str(run_index)].values.tolist()
    data = execute['run0'].values.tolist()
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

    delete_temp_files = params["delete_temp_files"].get_value(0)

    #project_name = params["project_name"].get_value(0)
    #geometry_folder = params["geometry_folder"].get_value(0)
    geometry_folder = params_mod["geometry_folder"]
    geometry_name_list_ranges = [0, 1, 3, 5, 8, 11, 14]
    building_list_name = params["building_list_name"].get_value(0)
    geometry_format = params["geometry_format"].get_value(0)
    terrain_folder = params["terrain_folder"].get_value(0)
    terrain_list_name = params["terrain_list_name"].get_value(0)
    if geometry_folder == 'LoD2':
        terrain_list_name += '_rta'
    #weather_folder = params["weather_folder"].get_value(0)
    weather_file = params["weather_file"].get_value(0)
    weatherfilepath = os.path.join(cea_path, 'databases\CH\Weather', weather_file)
    material_folder = params["material_folder"].get_value(0)
    material_list_name = params["material_list_name"].get_value(0)

    # Simulation parameters
    n_cores = int(params["n_cores"])
    n_core_list = range(n_cores)
    #xdim = int(params["xdim"])
    #ydim = int(params["ydim"])
    xdim = params_mod['spr']
    ydim = params_mod['spr']

    roof_resolution_increase = float(params["roof_resolution_increase"])
    max_roof_angle = float(params["max_roof_angle"])

    offset = 0.1
    time_list = []
    #params = mod_rad_params(params, rad_param_name, rad_param_value)

    # rend. time    (min, fast, acc, max)
    rad_n = float(params["rad_n"])       # Set the ambient accuracy to acc. This value will approximately equal the error from indirect illuminance interpolation. A value of zero implies no interpolation.
    rad_af = params["rad_af"].get_value(0)
    #rad_ab = float(params["rad_ab"])      # dir. pr.      (0,0.4.8) the number of ambient bounces to N. This is the maximum number of diffuse bounces computed by the indirect calculation. A value of zero implies no indirect calculation.
    #rad_ad = float(params["rad_ad"])   # dir. pr.      (0,32,512,4096) Set the number of ambient divisions to N. The error in the Monte Carlo calculation of indirect illuminance will be inversely proportional to the square root of this number. A value of zero implies no indirect calculation.
    rad_as = float(params["rad_as"])     # dir. pr.      (0,32,256,1024) Set the number of ambient super-samples to N. Super-samples are applied only to the ambient divisions which show a significant change.
    #rad_ar = float(params["rad_ar"])    # dir. ovpr.    (8,32,128,0) Set the ambient resolution to res. This number will determine the maximum density of ambient values used in interpolation. Error will start to increase on surfaces spaced closer than the scene size divided by the ambient resolution. The maximum ambient value density is the scene size times the ambient accuracy (see the -aa option below) divided by the ambient resolution. The scene size can be determined using getinfo(1) with the -d option on the input octree.
    #rad_aa = float(params["rad_aa"])    # dir. ovpr.    (.5,.2,.15,0) Set the ambient accuracy to acc. This value will approximately equal the error from indirect illuminance interpolation. A value of zero implies no interpolation.
    rad_lr = float(params["rad_lr"])      # min.          (0,4,8,16) Limit reflections to a maximum of N.
    rad_st = float(params["rad_st"])   # min.          (1,.85,.15,0) Set the specular sampling threshold to frac. This is the minimum fraction of reflection or transmission, under which no specular sampling is performed. A value of zero means that highlights will always be sampled by tracing reflected or transmitted rays. A value of one means that specular sampling is never used. Highlights from light sources will always be correct, but reflections from other surfaces will be approximated using an ambient value. A sampling threshold between zero and one offers a compromise between image accuracy and rendering time.
    rad_sj = float(params["rad_sj"])    #               (0,.3,.7,1) Set the specular sampling jitter to frac. This is the degree to which the highlights are sampled for rough specular materials. A value of one means that all highlights will be fully sampled using distributed ray tracing. A value of zero means that no jittering will take place, and all reflections will appear sharp even when they should be diffuse.
    rad_lw = float(params["rad_lw"])  # min.          (.05,.01,.002,0) Limit the weight of each ray to a minimum of frac. During ray-tracing, a record is kept of the final contribution a ray would have to the image. If it is less then the specified minimum, the ray is not traced.
    rad_dj = float(params["rad_dj"])   #               (0,0,.7,1)
    rad_ds = float(params["rad_ds"])    # inv. pr.      (0,0.5,.15,.02) Set the direct sampling ratio to frac. A light source will be subdivided until the width of each sample area divided by the distance to the illuminated point is below this ratio. This assures accuracy in regions close to large area sources at a slight computational expense. A value of zero turns source subdivision off, sending at most one shadow ray to each light source
    rad_dr = float(params["rad_dr"])      # dir. ~pr.     (0,1,3,6) Set the number of relays for secondary sources to N. A value of 0 means that secondary sources will be ignored. A value of 1 means that sources will be made into first generation secondary sources; a value of 2 means that first generation secondary sources will also be made into second generation secondary sources, and so on.
    rad_dp = float(params["rad_dp"])    # min.             (32,64,512,0) Set the secondary source presampling density to D. This is the number of samples per steradian that will be used to determine ahead of time whether or not it is worth following shadow rays through all the reflections and/or transmissions associated with a secondary source path. A value of 0 means that the full secondary source path will always be tested for shadows if it is tested at al

    rad_aa = params_mod['rad_aa']
    rad_ab = params_mod['rad_ab']
    rad_ad = params_mod['rad_ad']
    rad_ar = params_mod['rad_ar']

    # override

    # =============================== Preface =============================== #


    #results_path = os.path.join(case_path, project_name)
    #if not os.path.exists(results_path):
    #    os.makedirs(results_path)

    if os.path.exists(os.path.join(results_path, "log.txt")):
        os.remove(os.path.join(results_path, "log.txt"))

    buildings_path = os.path.join(results_path, "buildings")
    if not os.path.exists(buildings_path):
        os.makedirs(buildings_path)

    temp_path = os.path.join(results_path, "temp")
    if not os.path.exists(temp_path):
        os.makedirs(temp_path)

    if not os.path.exists(os.path.join(temp_path, "geometry")):
        os.makedirs(os.path.join(temp_path, "geometry"))

    bui_name_list = []
    rad = py2radiance.Rad(os.path.join(current_path, 'base.rad'), os.path.join(current_path, 'py2radiance_data'))

    ex_import = True
    ex_sim = True
    ex_rework = True



    if ex_import:
        # =============================== Import =============================== #
        # print project_name
        log(("scenario name:", scenario_name, "rta:", rta), '\n', write_log, results_path)
        log(("daysim parameters:", rad_n, rad_af, rad_ab, rad_ad, rad_as, rad_ar, rad_aa, rad_lr,
             rad_st, rad_sj, rad_lw, rad_dj, rad_ds, rad_dr, rad_dp), '\n', write_log, results_path)

        time1 = time.clock()

        mat_list = pd.read_csv(os.path.join(input_path, material_folder, material_list_name+".csv"), sep=',')
        mat_name_list = mat_list['name'].tolist()
        mat_value_list = mat_list['value'].tolist()

        if geometry_format == "shp":

            # import terrain
            print "Import terrain"
            terrain_path = os.path.join(input_path, "terrain_polygonised.gml\\terrain_polygonised.shp")
            # should be "DN" elevation index
            terrain_faces = shp2citygml.terrain2d23d_tin(terrain_path, "DN")
            faces2pointlist(os.path.join(results_path, "terrain_points.csv"), ["terrain"], "terrain", terrain_faces,
                            "terrain")
            terrain_name_list_path = os.path.join(input_path, 'terrain', "terrain_list.csv")
            terrain_list = pd.read_csv(terrain_name_list_path, sep=',')
            terrain_name_list = terrain_list['name'].tolist()
            terrain_mat_list = terrain_list['mat'].tolist()
            terrain_solids = [1]
            terrain_faces = [terrain_faces]

            print "elapsed time", round((time.clock() - time1) / 60, 1), " min" '\n'
            time_list.append(round((time.clock() - time1) / 60, 1))

            time1 = time.clock()
            # import buildings list
            db = dbfread.DBF(os.path.join(input_path, 'building\\cs.dbf'), load=True)
            for row in range(0, len(db)):
                bui_name_list.append(db.records[row]['Name'])

            bui_name_list_path = os.path.join(input_path, 'building', "bui_list.csv")
            if not os.path.exists(bui_name_list_path):
                bui_name_list = pd.DataFrame(bui_name_list)
                bui_name_list.to_csv(bui_name_list_path, sep=',', index=None)

            bui_list = pd.read_csv(bui_name_list_path, sep=',')
            bui_name_list = bui_list['name'].tolist()
            bui_mat_list = bui_list['mat'].tolist()

            mat_list = pd.read_csv(bui_name_list_path, sep=',')
            mat_name_list = mat_list['name'].tolist()
            mat_value_list = mat_list['value'].tolist()
            print mat_name_list, mat_value_list

            # import buildings
            print "Import buildings"
            building_path = os.path.join(input_path, "building\\cs.shp")
            building_solids = shp2citygml.building2d23d(building_path, "height_ag", terrain_faces[0])
            bui_int = 0

            face_list = [[]]*len(bui_name_list)
            normal_list = [[]]*len(bui_name_list)
            for bui_name in bui_name_list:
                bui_faces = py3dmodel.fetch.faces_frm_solid(building_solids[bui_int])
                fac_int = 0
                for f in bui_faces:
                    normal = face_normal(f, fac_int)
                    face_list[bui_int].append(f)
                    normal_list[bui_int].append(normal)
                    fac_int += 1


                print str(bui_name)
                faces2pointlist(os.path.join(results_path, "bui_points.csv"),bui_name_list, str(bui_name),
                bui_faces, "building")
                StlAPI_Writer().Write(building_solids[bui_int], os.path.join(temp_path, "geometry",
                                                                   str(bui_name)+'.stl'), False)

                bui_int += 1




            buildingsolids_lists = [0] * n_cores
            face_lists = [0] * n_cores
            normal_lists = [0] * n_cores
            bui_name_lists = [0] * n_cores
            bui_mat_lists = [0] * n_cores

            batch_length = int(round(len(building_solids)/n_cores,0))
            for n in range(n_cores-1):
                face_lists[n] = face_list[n*batch_length:(n+1)*batch_length]
                normal_lists[n] = normal_list[n * batch_length:(n + 1) * batch_length]
                buildingsolids_lists[n] = building_solids[n*batch_length:(n+1)*batch_length]
                bui_name_lists[n] = bui_name_list[n * batch_length:(n + 1) * batch_length]
                bui_mat_lists[n] = bui_mat_list[n * batch_length:(n + 1) * batch_length]

            face_lists[n_cores-1] = face_list[(n_cores-1)*batch_length:]
            normal_lists[n_cores-1] = normal_list[(n_cores-1)*batch_length:]
            buildingsolids_lists[n_cores-1] = building_solids[(n_cores-1)*batch_length:]
            bui_name_lists[n_cores - 1] = bui_name_list[(n_cores - 1) * batch_length:]
            bui_mat_lists[n_cores - 1] = bui_mat_list[(n_cores - 1) * batch_length:]
            bui_mat_list = bui_mat_lists
            bui_name_list = bui_name_lists

            print "elapsed time", round((time.clock() - time1) / 60, 1), " min" '\n'
            time_list.append(round((time.clock() - time1) / 60, 1))

        if geometry_format == "stl":

            # import terrain
            time1 = time.clock()
            log("Import terrain", '', write_log, results_path)
            terrain_name_list, terrain_mat_list = create_geometry_lists(n_cores, "single",
                                                                        os.path.join(input_path, terrain_folder),
                                                                        terrain_list_name, rta, None)
            print terrain_name_list, terrain_mat_list
            terrain_solids, terrain_faces, dummy_normal, dummy_vol = import_stl(0, terrain_name_list,
                                                                     os.path.join(input_path, terrain_folder),
                                                                     "terrain")
            log(("elapsed time", round((time.clock() - time1) / 60, 1), " min"), '\n', write_log, results_path)
            time_list.append(round((time.clock() - time1) / 60, 1))

            # import buildings
            time1 = time.clock()
            log("Import buildings", '', write_log, results_path)
            bui_name_list, bui_mat_list = create_geometry_lists(n_cores, "multiple",
                                                                os.path.join(input_path, geometry_folder),
                                                                building_list_name, rta, geometry_name_list_ranges)

            face_lists = [0] * n_cores
            normal_lists = [0] * n_cores
            buildingsolids_lists = [0] * n_cores
            bui_vol = []

            for n_core in range(n_cores):
                buildingsolids_lists[n_core], face_lists[n_core], normal_lists[n_core], bui_vol_batch = import_stl(n_core, bui_name_list[n_core],
                                                                              os.path.join(input_path, geometry_folder),
                                                                              "building")
                bui_vol += bui_vol_batch
            flattened_bui_name_list = [val for sublist in bui_name_list for val in sublist]
            pd.DataFrame(bui_vol).T.to_csv(os.path.join(results_path, 'bui_vol.csv'), header=flattened_bui_name_list, index=None)

            log(("elapsed time", round((time.clock() - time1) / 60, 1), " min"), '\n', write_log, results_path)
            time_list.append(round((time.clock() - time1) / 60, 1))
    if ex_sim:
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
        multiprocess('1lists', generate_sensor_points, ("n_core", results_path, write_log, bui_name_list, face_lists,
                                                        normal_lists, xdim, ydim, offset, roof_resolution_increase,
                                                        max_roof_angle), [n_core_list])
        rad.create_rad_input_file()
        droplist_ad = []
        # Execute daysim
        log("\nDaysim evaluation",'', write_log, results_path)
        multiprocess('1lists', execute_daysim, ("n_core", results_path, write_log, rad, weatherfilepath, rad_n, rad_af,
                                                rad_ab, rad_ad, rad_as, rad_ar, rad_aa, rad_lr, rad_st, rad_sj, rad_lw,
                                                rad_dj, rad_ds, rad_dr, rad_dp, mat_name_list, mat_value_list),
                     [n_core_list])
        log(("elapsed time", round((time.clock() - time1) / 60, 1), " min"), '\n', write_log, results_path)
        time_list.append(round((time.clock() - time1) / 60, 1))

    if ex_rework:
        # =============================== Rework =============================== #
        '''
        spatial_time_average_list = ["hour", "day", "month", "year"]
        spatial_average_list = ["bui_fac", "sen", "bui"]
        '''
        ''''''
        # fast
        spatial_time_average_list = ['hour', "month", 'year']
        spatial_average_list = ['bui', "bui_fac"]

        chunk_size_concat = 2500
        # res 5 --> 4400 (half the days), res 2 --> 4400/25*4 = 700
        chunk_size_bui = int(2200 * params_mod['spr'])

        # time averaging
        time1 = time.clock()

        log("\n Time averaging", '', write_log, results_path)
        multiprocess('1lists', time_sums, ("n_core", results_path), [n_core_list])
        log(("\n elapsed time", round((time.clock() - time1) / 60, 1), " min"), '\n', write_log, results_path)
        time_list.append(round((time.clock() - time1) / 60, 1))

        # spatial averaging
        time1 = time.clock()
        log("\n Spatial averaging", '', write_log, results_path)
        multiprocess("3lists", sen_average, ("n_core", "item1", "item2", n_cores, results_path, write_log),
                     [n_core_list, spatial_time_average_list, spatial_average_list])
        # save sensor and id_df files per building in 'buildings' folder

        multiprocess('1lists', bui_id_df_per_building, ("n_core", results_path), [n_core_list])
        multiprocess('1lists', hourly_file_per_building, ("n_core", n_cores, results_path, chunk_size_bui), [n_core_list])


        log(("\n elapsed time", round((time.clock() - time1) / 60, 1), " min"), '\n', write_log, results_path)
        time_list.append(round((time.clock() - time1) / 60, 1))

        # coacentate
        time1 = time.clock()
        log("\n Coacenating", '', write_log, results_path)
        # concat spatial and time lists
        #spatial_average_list = ["bui_fac", "bui_fac_tot", "bui_fac_rel", "sen", "bui"]
        multiprocess("2lists", concat_results, ("item1", "item2", n_cores, results_path, chunk_size_concat, write_log),
                     [spatial_time_average_list, spatial_average_list])
        # concat bui_id_df files
        bui_id_df = pd.DataFrame()
        for n in range(n_cores):
            bui_id_df_batch = pd.read_csv(os.path.join(results_path, "temp", 'bui_id_df_' + str(n) + '.csv'), sep=',')
            bui_id_df = pd.concat((bui_id_df, bui_id_df_batch), axis=0)
        bui_id_df.to_csv(os.path.join(results_path, 'bui_id_df.csv'), header=True, index=None)
        # concat building_points file
        faces_all = pd.DataFrame()
        last_int = 0
        for n in range(n_cores):
            faces = pd.read_csv(os.path.join(results_path, "temp", 'building_points_' + str(n) + '.csv'), sep=',',
                                header=None)
            faces.iloc[:, 1] += last_int
            faces_all = pd.concat((faces_all, faces), axis=0)
            last_int = faces.iloc[-1, 1]+1
        faces_all.to_csv(os.path.join(results_path, 'building_points.csv'), header=None, index=None)

        # concat shading frac
        frac = pd.DataFrame()
        for n in range(n_cores):
            add = pd.read_csv(os.path.join(results_path, "temp", 'sen_day_' + str(n) + '.csv'), sep=',', header=None,
                               nrows=1)
            print add
            frac = pd.concat([frac, add], axis=1)
        frac[frac > 0] = 1
        frac = frac.astype(int)
        frac.to_csv(os.path.join(results_path, 'sen_not_shaded.csv'), header=None, index=None, )

        # concat face relative
        bui_fac_rel = pd.DataFrame()
        for n in range(n_cores):
            bui_fac_rel_batch = pd.read_csv(os.path.join(results_path, "temp", 'bui_fac_rel_month_' + str(n) + '.csv'), sep=',')
            bui_fac_rel = pd.concat((bui_fac_rel, bui_fac_rel_batch), axis=1)
        bui_fac_rel.to_csv(os.path.join(results_path, 'bui_fac_rel_month.csv'), header=None, index=None)


        # rename bui hour
        bui_hour = pd.read_csv(os.path.join(results_path, 'bui_hour.csv'), header=None)
        index = ['T'+str(x+1) for x in bui_hour.index.values.tolist()]
        bui_hour['index'] = index
        bui_hour = bui_hour.set_index('index')
        bui_hour = bui_hour.T
        header = pd.read_csv(os.path.join(results_path, 'bui_vol.csv')).columns
        bui_hour['Name'] = header
        bui_hour = bui_hour.set_index('Name')
        bui_hour.to_csv(os.path.join(results_path, 'radiation.csv'))

        log(("\n elapsed time", round((time.clock() - time1) / 60, 1), " min"), '\n', write_log, results_path)
        time_list.append(round((time.clock() - time1) / 60, 1))

        log(("total time", round((time.clock()-time0)/60, 1), " min"), '\n', write_log, results_path)
        time_list.append(round((time.clock() - time0) / 60, 1))

        pd.DataFrame(time_list).to_csv(os.path.join(results_path, 'time_list.csv'), header=None, index=None)
        ''''''
        if delete_temp_files == "delete":
            for an_core in range(n_cores):
                shutil.rmtree(os.path.join(results_path, 'daysim_data' + str(an_core)))
            shutil.rmtree(os.path.join(results_path, 'temp'))


if __name__ == '__main__':

    path = r'C:\Users\Assistenz\Desktop\161117_Radiaiton_code_paul_neitzel'
    case = 'case_study'
    scenario_name = 'base'
    geometry_folder = 'LoD2'

    spr = 10
    rad_aa = 0.3
    rad_ab = 2
    rad_ad = 16
    rad_ar = 16
    run_params = {'geometry_folder': geometry_folder, 'spr': spr,
                                'rad_aa': rad_aa, 'rad_ab': rad_ab, 'rad_ad': rad_ad,
                                'rad_ar': rad_ar}

    calc_radiation(path, case, scenario_name, run_params)
