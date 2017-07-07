from cea.resources.radiation_arcgis.radiation import _CalcRadiationAllDays


def calculate_radiation_for_all_days(T_G_day, aspect_slope, dem_rasterfinal_path, heightoffset, latitude, locator,
                                     observers_path, path_arcgis_db):

    # let's just be sure this is set
    arcpy.env.workspace = path_arcgis_db
    arcpy.env.overwriteOutput = True
    arcpy.CheckOutExtension("spatial")

    T_G_day_path = locator.get_temporary_file('T_G_day.pickle')
    T_G_day.to_pickle(T_G_day_path)

    temporary_folder = locator.get_temporary_folder()

    import multiprocessing
    process = multiprocessing.Process(target=_CalcRadiationAllDays, args=(
        T_G_day_path, aspect_slope, dem_rasterfinal_path, heightoffset, latitude, observers_path, path_arcgis_db,
        temporary_folder))
    process.start()
    process.join()  ## block until process terminates
    if process.exitcode != 0:
        raise AssertionError('_CalcRadiationAllDays failed...')