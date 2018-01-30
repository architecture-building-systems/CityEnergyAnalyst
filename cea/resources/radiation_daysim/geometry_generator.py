"""
Geometry generator from
Shapefiles (buiding footprint)
and .tiff (terrain)

into 3D geometry with windows and roof equivalent to LOD3

"""
import pyliburo.py3dmodel.construct as construct
import pyliburo.py3dmodel.fetch as fetch
import pyliburo.py3dmodel.calculate as calculate
from pyliburo import py3dmodel as py3dmodel
import pyliburo.py3dmodel.modify as modify
import math

import pyliburo.gml3dmodel as gml3dmodel

from OCC.IntCurvesFace import IntCurvesFace_ShapeIntersector
from OCC.gp import gp_Pnt, gp_Lin, gp_Ax1, gp_Dir
from geopandas import GeoDataFrame as gdf

import cea.inputlocator
import cea.config
import numpy as np
import gdal
import time

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Kian Wee Chen"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def identify_surfaces_type(occface_list):

    roof_list = []
    footprint_list = []
    facade_list_north = []
    facade_list_west = []
    facade_list_east = []
    facade_list_south = []
    vec_vertical = (0, 0, 1)
    vec_horizontal = (0, 1, 0)

    # distinguishing between facade, roof and footprint.
    for f in occface_list:
        # get the normal of each face
        n = py3dmodel.calculate.face_normal(f)
        flatten_n = [n[0],n[1],0] # need to flatten to erase Z just to consider vertical surfaces.
        angle_to_vertical = py3dmodel.calculate.angle_bw_2_vecs(vec_vertical, n)
        # means its a facade
        if angle_to_vertical > 45 and angle_to_vertical < 135:
            angle_to_horizontal = py3dmodel.calculate.angle_bw_2_vecs_w_ref(vec_horizontal, flatten_n, vec_vertical)
            if (0 <= angle_to_horizontal <= 45) or (315 <= angle_to_horizontal <= 360):
                facade_list_north.append(f)
            elif (45 < angle_to_horizontal < 135):
                facade_list_west.append(f)
            elif (135 <= angle_to_horizontal <= 225):
                facade_list_south.append(f)
            elif 225 < angle_to_horizontal < 315:
                facade_list_east.append(f)
        elif angle_to_vertical <= 45:
            roof_list.append(f)
        elif angle_to_vertical >= 135:
            footprint_list.append(f)

    return facade_list_north, facade_list_west, facade_list_east, facade_list_south, roof_list, footprint_list

def calc_intersection(terrain_intersection_curves, edges_coords, edges_dir):
    """
    This script calculates the intersection of the building edges to the terrain,
    :param terrain_intersection_curves:
    :param edges_coords:
    :param edges_dir:
    :return: intersecting points, intersecting faces
    """
    building_line = gp_Lin(gp_Ax1(gp_Pnt(edges_coords[0], edges_coords[1], edges_coords[2]),
                                  gp_Dir(edges_dir[0], edges_dir[1], edges_dir[2])))
    terrain_intersection_curves.PerformNearest(building_line, 0.0, float("+inf"))
    if terrain_intersection_curves.IsDone():
        npts = terrain_intersection_curves.NbPnt()
        if npts !=0:
            return terrain_intersection_curves.Pnt(1), terrain_intersection_curves.Face(1)
        else:
            return None, None
    else:
        return None, None

def create_windows(surface, wwr, ref_pypt):
    scaler = math.sqrt(wwr)
    return fetch.shape2shapetype(modify.uniform_scale(surface, scaler, scaler, scaler, ref_pypt))

def create_hollowed_facade(surface_facade, window):
    b_facade_cmpd = fetch.shape2shapetype(construct.boolean_difference(surface_facade, window))
    hole_facade = fetch.geom_explorer(b_facade_cmpd, "face")[0]
    normal2 = py3dmodel.calculate.face_normal(hole_facade)
    hollowed_facade = construct.simple_mesh(hole_facade)
    #Clean small triangles: this is a despicable source of error
    hollowed_facade_clean = [x for x in hollowed_facade if calculate.face_area(x) > 1E-3]

    return hollowed_facade_clean, hole_facade



def building2d23d(locator, geometry_terrain, settings, height_col, nfloor_col):
    """
    :param locator: InputLocator - provides paths to files in a scenario
    :type locator: cea.inputlocator.InputLocator
    :param settings: parameters that configure the level of simplification of geometry
    :type settings: cea.config.Section
    :param height_col: name of the columns storing the height of buildings
    :param nfloor_col: name ofthe column storing the number of floors in buildings.
    :return:
    """

    district_shp_path = locator.get_district_geometry()

    # path to zone geometry database
    zone_shp_path = locator.get_zone_geometry()

    # path to database of architecture properties
    architecture_dbf_path = locator.get_building_architecture()

    # read district shapefile and names of buildings of the zone of analysis
    district_building_records = gdf.from_file(district_shp_path).set_index('Name')
    district_building_names = district_building_records.index.values
    zone_building_names = locator.get_zone_building_names()
    architecture_wwr = gdf.from_file(architecture_dbf_path).set_index('Name')

    #make shell out of tin_occface_list and create OCC object
    terrain_shell = construct.make_shell_frm_faces(geometry_terrain)[0]
    terrain_intersection_curves = IntCurvesFace_ShapeIntersector()
    terrain_intersection_curves.Load(terrain_shell, 1e-6)

    #empty list where to store the closed geometries
    geometry_3D_zone = []
    geometry_3D_surroundings = []

    for name in district_building_names:
        height = float(district_building_records.loc[name, height_col])
        nfloors = int(district_building_records.loc[name, nfloor_col])

        # simplify geometry tol =1 for buildings of interest, tol = 5 for surroundings
        if (name in zone_building_names) and settings.consider_floors:
            range_floors = range(nfloors+1)
            flr2flr_height = height / nfloors
            geometry = district_building_records.ix[name].geometry.simplify(settings.zone_geometry,
                                                                            preserve_topology=True)
        else:
            range_floors = [0,1]
            flr2flr_height = height
            geometry = district_building_records.ix[name].geometry.simplify(settings.surrounding_geometry,
                                                                            preserve_topology=True)

        # burn buildings footprint into the terrain and return the location of the new face
        face_footprint = burn_buildings(geometry, terrain_intersection_curves)

        # create floors and form a solid
        building_solid = calc_solid(face_footprint, range_floors, flr2flr_height)

        # now get all surfaces and create windows only if the buildings are in the area of study
        window_list =[]
        wall_list = []
        orientation = []
        orientation_win = []
        normals_w = []
        normals_win = []
        if (name in zone_building_names):
            if (settings.consider_windows):
                # identify building surfaces according to angle:
                face_list = py3dmodel.fetch.faces_frm_solid(building_solid)
                facade_list_north, facade_list_west, \
                facade_list_east, facade_list_south, roof_list, footprint_list = identify_surfaces_type(face_list)

                # get window properties
                wwr_west = architecture_wwr.ix[name, "wwr_west"]
                wwr_east = architecture_wwr.ix[name, "wwr_east"]
                wwr_north = architecture_wwr.ix[name, "wwr_north"]
                wwr_south = architecture_wwr.ix[name, "wwr_south"]

                window_west, wall_west, normals_windows, normals_walls = calc_windows_walls(facade_list_west, wwr_west)
                if len(window_west) != 0:
                    window_list.extend(window_west)
                    orientation_win.extend(['west'] * len(window_west))
                    normals_win.extend(normals_windows)
                wall_list.extend(wall_west)
                orientation.extend(['west']*len(wall_west))
                normals_w.extend(normals_walls)

                window_east, wall_east, normals_windows, normals_walls  = calc_windows_walls(facade_list_east, wwr_east)
                if len(window_east) != 0:
                    window_list.extend(window_east)
                    orientation_win.extend(['east'] * len(window_east))
                    normals_win.extend(normals_windows)
                wall_list.extend(wall_east)
                orientation.extend(['east'] * len(wall_east))
                normals_w.extend(normals_walls)

                window_north, wall_north, normals_windows_north, normals_walls_north  = calc_windows_walls(facade_list_north, wwr_north)
                if len(window_north) != 0:
                    window_list.extend(window_north)
                    orientation_win.extend(['north'] * len(window_north))
                    normals_win.extend(normals_windows_north)
                wall_list.extend(wall_north)
                orientation.extend(['north'] * len(wall_north))
                normals_w.extend(normals_walls_north)

                window_south, wall_south, normals_windows_south, normals_walls_south  = calc_windows_walls(facade_list_south, wwr_south)
                if len(window_south) != 0:
                    window_list.extend(window_south)
                    orientation_win.extend(['south'] * len(window_south))
                    normals_win.extend(normals_windows_south)
                wall_list.extend(wall_south)
                orientation.extend(['south'] * len(wall_south))
                normals_w.extend(normals_walls_south)


                geometry_3D_zone.append({"name": name, "windows": window_list, "walls": wall_list, "roofs": roof_list,
                                     "footprint": footprint_list, "orientation_walls":orientation, "orientation_windows":orientation_win,
                                         "normals_windows":normals_win, "normals_walls": normals_w })

            else:
                facade_list, roof_list, footprint_list = gml3dmodel.identify_building_surfaces(building_solid)
                wall_list = facade_list
                geometry_3D_zone.append({"name": name, "windows": window_list, "walls": wall_list, "roofs": roof_list,
                                     "footprint": footprint_list, "orientation_walls":orientation, "orientation_windows":orientation_win,
                                         "normals_windows":normals_win, "normals_walls": normals_w})

            # DO this to visualize progress while debugging!:
            # edges1 = calculate.visualise_face_normal_as_edges(wall_list,5)
            # edges2 = calculate.visualise_face_normal_as_edges(roof_list, 5)
            # edges3 = calculate.visualise_face_normal_as_edges(footprint_list, 5)
            # construct.visualise([wall_list, roof_list ,footprint_list , edges1, edges2, edges3],["WHITE","WHITE","WHITE","BLACK", "BLACK","BLACK"])
        else:
            facade_list, roof_list, footprint_list = gml3dmodel.identify_building_surfaces(building_solid)
            wall_list = facade_list
            geometry_3D_surroundings.append({"name": name, "windows": window_list, "walls": wall_list, "roofs": roof_list,
                                 "footprint": footprint_list, "orientation_walls":orientation, "orientation_windows":orientation_win,
                                  "normals_windows":normals_win, "normals_walls": normals_w})

            ## DO this to visualize progress while debugging!:
            # edges1 = calculate.visualise_face_normal_as_edges(wall_list,5)
            # edges2 = calculate.visualise_face_normal_as_edges(roof_list, 5)
            # edges3 = calculate.visualise_face_normal_as_edges(footprint_list, 5)
            # construct.visualise([wall_list, roof_list ,footprint_list , edges1, edges2, edges3],["WHITE","WHITE","WHITE","BLACK", "BLACK","BLACK"])
    return geometry_3D_zone, geometry_3D_surroundings


def burn_buildings(geometry, terrain_intersection_curves):
    point_list_2D = list(geometry.exterior.coords)
    point_list_3D = [(a, b, 0) for (a, b) in point_list_2D]  # add 0 elevation

    # creating floor surface in pythonocc
    face = construct.make_polygon(point_list_3D)
    # get the midpt of the face
    face_midpt = calculate.face_midpt(face)

    # project the face_midpt to the terrain and get the elevation
    inter_pt, inter_face = calc_intersection(terrain_intersection_curves, face_midpt, (0, 0, 1))

    # reconstruct the footprint with the elevation
    loc_pt = fetch.occpt2pypt(inter_pt)
    face = fetch.shape2shapetype(modify.move(face_midpt, loc_pt, face))
    return face

def calc_solid(face_footprint, range_floors, flr2flr_height):

    # create faces for every floor and extrude the solid
    moved_face_list = []
    for floor_counter in range_floors:
        dist2mve = floor_counter * flr2flr_height
        # get midpt of face
        orig_pt = calculate.face_midpt(face_footprint)
        # move the pt 1 level up
        dest_pt = modify.move_pt(orig_pt, (0, 0, 1), dist2mve)
        moved_face = modify.move(orig_pt, dest_pt, face_footprint)
        moved_face_list.append(moved_face)

    # make checks to satisfy a closed geometry also called a shell

    vertical_shell = construct.make_loft(moved_face_list)
    vertical_face_list = fetch.geom_explorer(vertical_shell, "face")
    roof = moved_face_list[-1]
    footprint = moved_face_list[0]
    all_faces = []
    all_faces.append(footprint)
    all_faces.extend(vertical_face_list)
    all_faces.append(roof)
    building_shell_list = construct.make_shell_frm_faces(all_faces)

    # make sure all the normals are correct (they are pointing out)
    bldg_solid = construct.make_solid(building_shell_list[0])
    bldg_solid = modify.fix_close_solid(bldg_solid)

    ##dO this to visualize progress while debugging!:
    #face_list = fetch.geom_explorer(bldg_solid, "face")
    # edges = calculate.visualise_face_normal_as_edges(face_list,5)
    # construct.visualise([face_list,edges],["WHITE","BLACK"])
    return bldg_solid

def calc_windows_walls(facade_list, wwr):
    window_list = []
    wall_list = []
    normals_win = []
    normals_wall = []
    for surface_facade in facade_list:
        ref_pypt = calculate.face_midpt(surface_facade)
        standard_normal = py3dmodel.calculate.face_normal(surface_facade) # to avoid problems with fuzzy normals
        # offset the facade to create a window according to the wwr
        if 0.0 < wwr < 1.0:
            # for window
            window = create_windows(surface_facade, wwr, ref_pypt)
            window_list.append(window)
            normals_win.append(standard_normal)
            # for walls
            hollowed_facade, hole_facade = create_hollowed_facade(surface_facade, window)  # accounts for hole created by window
            wall_list.extend(hollowed_facade)
            normals_wall.extend([standard_normal]*len(hollowed_facade))

        elif wwr == 1.0:
            window_list.append(surface_facade)
            normals_win.append(standard_normal)
        else:
            wall_list.append(surface_facade)
            normals_wall.append(standard_normal)

    return window_list, wall_list, normals_win, normals_wall

def raster2tin(input_terrain_raster):

    # read raster records
    raster_dataset = gdal.Open(input_terrain_raster)
    band = raster_dataset.GetRasterBand(1)
    a = band.ReadAsArray(0, 0, raster_dataset.RasterXSize, raster_dataset.RasterYSize)
    (y_index, x_index) = np.nonzero(a >= 0)
    (upper_left_x, x_size, x_rotation, upper_left_y, y_rotation, y_size) = raster_dataset.GetGeoTransform()
    x_coords = x_index * x_size + upper_left_x + (x_size / 2)  # add half the cell size
    y_coords = y_index * y_size + upper_left_y + (y_size / 2)  # to centre the point

    elevation_mean = int(a[y_index, x_index].mean())

    raster_points = [(x, y, z) for x, y, z in zip(x_coords, y_coords, a[y_index, x_index])]

    tin_occface_list = construct.delaunay3d(raster_points)

    return elevation_mean, tin_occface_list

def geometry_main(locator, simplification_params):

    # list of faces of terrain
    elevation_mean, geometry_terrain = raster2tin(locator.get_terrain())

    # transform buildings 2D to 3D and add windows
    geometry_3D_zone, geometry_3D_surroundings = building2d23d(locator, geometry_terrain, simplification_params, height_col='height_ag',
                                                               nfloor_col="floors_ag")

    return elevation_mean, geometry_terrain, geometry_3D_zone, geometry_3D_surroundings

if __name__ == '__main__':
    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    settings = config.radiation_daysim

    # run routine City GML LOD 1
    time1 = time.time()
    elevation_mean, geometry_terrain, geometry_3D_zone, geometry_3D_surroundings = geometry_main(locator, settings)
    print("Geometry of the scene created in %.2f mins" % (time.time() - time1) / 60.0)


    # to visualize the results
    geometry_buildings = []
    windows = [val for sublist in geometry_3D_zone for val in sublist['windows']]
    walls = [val for sublist in geometry_3D_zone for val in sublist['walls']]
    roofs = [val for sublist in geometry_3D_zone for val in sublist['roofs']]
    footprint = [val for sublist in geometry_3D_zone for val in sublist['footprint']]
    walls_s = [val for sublist in geometry_3D_surroundings  for val in sublist['walls']]
    windows_s = [val for sublist in geometry_3D_surroundings for val in sublist['windows']]
    roof_s = [val for sublist in geometry_3D_surroundings for val in sublist['roofs']]

    geometry_buildings.extend(windows)
    geometry_buildings.extend(walls)
    geometry_buildings.extend(roofs)
    geometry_buildings.extend(footprint)
    geometry_buildings.extend(walls_s)
    geometry_buildings.extend(windows_s)
    geometry_buildings.extend(roof_s)

    # DO this to visualize progress while debugging!:
    #normals_terrain = calculate.visualise_face_normal_as_edges(geometry_terrain,5)
    construct.visualise([geometry_terrain, geometry_buildings], ["BLUE","WHITE"]) #install Wxpython



