"""
Geometry generator from
Shapefiles (building footprint)
and .tiff (terrain)

into 3D geometry with windows and roof equivalent to LOD3

"""
import math
import os
import pickle
import time
from itertools import repeat

import numpy as np
import pandas as pd
import py4design.py3dmodel.calculate as calculate
import py4design.py3dmodel.construct as construct
import py4design.py3dmodel.fetch as fetch
import py4design.py3dmodel.modify as modify
import py4design.py3dmodel.utility as utility
from OCC.Core.IntCurvesFace import IntCurvesFace_ShapeIntersector
from OCC.Core.gp import gp_Pnt, gp_Lin, gp_Ax1, gp_Dir
from osgeo import osr, gdal
from py4design import urbangeom

import cea
import cea.config
import cea.inputlocator
import cea.utilities.parallel

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Kian Wee Chen"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

from cea.utilities.standardize_coordinates import (get_lat_lon_projected_shapefile, get_projected_coordinate_system,
                                                   crs_to_epsg)


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
        n = calculate.face_normal(f)
        flatten_n = [n[0], n[1], 0]  # need to flatten to erase Z just to consider vertical surfaces.
        angle_to_vertical = calculate.angle_bw_2_vecs(vec_vertical, n)
        # means its a facade
        if angle_to_vertical > 45 and angle_to_vertical < 135:
            angle_to_horizontal = calculate.angle_bw_2_vecs_w_ref(vec_horizontal, flatten_n, vec_vertical)
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


def calc_intersection(surface, edges_coords, edges_dir, tolerance):
    """
    This script calculates the intersection of the building edges to the terrain,
    """
    point = gp_Pnt(edges_coords[0], edges_coords[1], edges_coords[2])
    direction = gp_Dir(edges_dir[0], edges_dir[1], edges_dir[2])
    line = gp_Lin(gp_Ax1(point, direction))

    terrain_intersection_curves = IntCurvesFace_ShapeIntersector()
    terrain_intersection_curves.Load(surface, tolerance)
    terrain_intersection_curves.PerformNearest(line, float("-inf"), float("+inf"))

    if terrain_intersection_curves.IsDone():
        npts = terrain_intersection_curves.NbPnt()
        if npts != 0:
            return terrain_intersection_curves.Pnt(1), terrain_intersection_curves.Face(1)
        else:
            return None, None
    else:
        return None, None


def create_windows(surface, wwr, ref_pypt):
    scaler = math.sqrt(wwr)
    return fetch.topo2topotype(modify.uniform_scale(surface, scaler, scaler, scaler, ref_pypt))


def create_hollowed_facade(surface_facade, window):
    b_facade_cmpd = fetch.topo2topotype(construct.boolean_difference(surface_facade, window))
    hole_facade = fetch.topo_explorer(b_facade_cmpd, "face")[0]
    hollowed_facade = construct.simple_mesh(hole_facade)
    # Clean small triangles: this is a despicable source of error
    hollowed_facade_clean = [x for x in hollowed_facade if calculate.face_area(x) > 1E-3]

    return hollowed_facade_clean, hole_facade


def calc_building_solids(buildings_df, geometry_simplification, elevation_map, num_processes):
    height_col_name = 'height_ag'
    nfloor_col_name = "floors_ag"

    # simplify geometry for buildings of interest
    geometries = buildings_df.geometry.simplify(geometry_simplification, preserve_topology=True)

    height = buildings_df[height_col_name].astype(float)
    nfloors = buildings_df[nfloor_col_name].astype(int)
    range_floors = nfloors.map(lambda floors: range(floors + 1))
    floor_to_floor_height = calc_floor_to_floor_height(height, nfloors)

    n = len(geometries)
    out = cea.utilities.parallel.vectorize(process_geometries, num_processes,
                                           on_complete=print_terrain_intersection_progress)(
        geometries, repeat(elevation_map, n), range_floors, floor_to_floor_height)

    solids, elevations = zip(*out)
    return list(solids), list(elevations)


def calc_floor_to_floor_height(building_height, number_of_floors):
    '''
    This function calculates the floor to floor height for a building.
    '''
    return building_height / number_of_floors


def process_geometries(geometry, elevation_map, range_floors, floor_to_floor_height):
    elevation_map_for_geometry = elevation_map.get_elevation_map_from_geometry(geometry)
    # burn buildings footprint into the terrain and return the location of the new face
    face_footprint, elevation = burn_buildings(geometry, elevation_map_for_geometry, 1e-12)
    # create floors and form a solid
    building_solid = calc_solid(face_footprint, range_floors, floor_to_floor_height)

    return building_solid, elevation


def calc_building_geometry_surroundings(name, building_solid, geometry_pickle_dir):
    facade_list, roof_list, footprint_list = urbangeom.identify_building_surfaces(building_solid)
    geometry_3D_surroundings = {"name": name,
                                "windows": [],
                                "walls": facade_list,
                                "roofs": roof_list,
                                "footprint": footprint_list,
                                "orientation_walls": [],
                                "orientation_windows": [],
                                "normals_windows": [],
                                "normals_walls": [],
                                "intersect_walls": []}

    building_geometry = BuildingGeometry(**geometry_3D_surroundings)
    building_geometry.save(os.path.join(geometry_pickle_dir, 'surroundings', str(name)))
    return name


def building_2d_to_3d(zone_df, surroundings_df, architecture_wwr_df, elevation_map, config, geometry_pickle_dir):
    # Config variables
    num_processes = config.get_number_of_processes()
    zone_simplification = config.radiation_usr.zone_geometry
    surroundings_simplification = config.radiation_usr.surrounding_geometry
    neglect_adjacent_buildings = config.radiation_usr.neglect_adjacent_buildings

    print('Calculating terrain intersection of building geometries')
    zone_buildings_df = zone_df.set_index('name')
    zone_building_names = zone_buildings_df.index.values
    zone_building_solid_list, zone_elevations = calc_building_solids(zone_buildings_df, zone_simplification,
                                                                     elevation_map, num_processes)

    surroundings_buildings_df = surroundings_df.set_index('name')
    surroundings_building_names = surroundings_buildings_df.index.values
    surroundings_building_solid_list, _ = calc_building_solids(surroundings_buildings_df, surroundings_simplification,
                                                               elevation_map, num_processes)

    # calculate geometry for the surroundings
    print('Generating geometry for surrounding buildings')
    geometry_3D_surroundings = [calc_building_geometry_surroundings(x, y, geometry_pickle_dir) for x, y in
                                zip(surroundings_building_names, surroundings_building_solid_list)]

    # calculate geometry for the zone of analysis
    print('Generating geometry for buildings in the zone of analysis')
    n = len(zone_building_names)
    calc_zone_geometry_multiprocessing = cea.utilities.parallel.vectorize(calc_building_geometry_zone,
                                                                          num_processes,
                                                                          on_complete=print_progress)

    if not neglect_adjacent_buildings:
        all_building_solid_list = np.append(zone_building_solid_list, surroundings_building_solid_list)
    else:
        all_building_solid_list = []
    geometry_3D_zone = calc_zone_geometry_multiprocessing(zone_building_names,
                                                          zone_building_solid_list,
                                                          repeat(all_building_solid_list, n),
                                                          repeat(architecture_wwr_df, n),
                                                          repeat(geometry_pickle_dir, n),
                                                          repeat(neglect_adjacent_buildings, n),
                                                          zone_elevations)

    return geometry_3D_zone, geometry_3D_surroundings


def print_progress(i, n, _, __):
    print("Generating geometry for building {i} completed out of {n}".format(i=i + 1, n=n))


def print_terrain_intersection_progress(i, n, _, __):
    print("Calculation of terrain intersection for building {i} completed out of {n}".format(i=i + 1, n=n))


def are_buildings_close_to_eachother(x_1, y_1, solid2):
    box2 = calculate.get_bounding_box(solid2)
    x_2 = box2[0]
    y_2 = box2[1]
    delta = math.sqrt((y_2 - y_1) ** 2 + (x_2 - x_1) ** 2)
    if delta <= 100:
        return True
    else:
        return False


class BuildingGeometry(object):
    __slots__ = ["name", "windows", "walls", "roofs", "footprint", "orientation_walls", "orientation_windows",
                 "normals_windows", "normals_walls", "intersect_walls", "terrain_elevation"]

    def __init__(self, **kwargs):
        for key in self.__slots__:
            value = kwargs.get(key)
            setattr(self, key, value)

    def __getstate__(self):
        return [getattr(self, k, None) for k in self.__slots__]

    def __setstate__(self, data):
        for k, v in zip(self.__slots__, data):
            setattr(self, k, v)

    @classmethod
    def load(cls, pickle_location):
        with open(pickle_location, 'rb') as fp:
            values = pickle.load(fp)
            obj = cls()
            obj.__setstate__(values)
        return obj

    def save(self, pickle_location):
        dir_name = os.path.dirname(pickle_location)
        os.makedirs(dir_name, exist_ok=True)

        with open(pickle_location, 'wb') as f:
            pickle.dump(self.__getstate__(), f)
        return pickle_location


def calc_building_geometry_zone(name, building_solid, all_building_solid_list, architecture_wwr_df,
                                geometry_pickle_dir, neglect_adjacent_buildings, elevation):
    # now get all surfaces and create windows only if the buildings are in the area of study
    window_list = []
    wall_list = []
    orientation = []
    orientation_win = []
    normals_walls = []
    normals_win = []
    intersect_wall = []

    # check if buildings are close together and it merits to check the intersection
    potentially_intersecting_solids = []
    if not neglect_adjacent_buildings:
        box = calculate.get_bounding_box(building_solid)
        x, y = box[0], box[1]
        for solid in all_building_solid_list:
            if are_buildings_close_to_eachother(x, y, solid):
                potentially_intersecting_solids.append(solid)

    # identify building surfaces according to angle:
    face_list = fetch.faces_frm_solid(building_solid)
    facade_list_north, facade_list_west, \
    facade_list_east, facade_list_south, roof_list, footprint_list = identify_surfaces_type(face_list)

    # get window properties
    wwr_west = architecture_wwr_df.loc[name, "wwr_west"]
    wwr_east = architecture_wwr_df.loc[name, "wwr_east"]
    wwr_north = architecture_wwr_df.loc[name, "wwr_north"]
    wwr_south = architecture_wwr_df.loc[name, "wwr_south"]

    window_west, \
    wall_west, \
    normals_windows_west, \
    normals_walls_west, \
    wall_intersects_west = calc_windows_walls(facade_list_west, wwr_west, potentially_intersecting_solids)
    if len(window_west) != 0:
        window_list.extend(window_west)
        orientation_win.extend(['west'] * len(window_west))
        normals_win.extend(normals_windows_west)
    wall_list.extend(wall_west)
    orientation.extend(['west'] * len(wall_west))
    normals_walls.extend(normals_walls_west)
    intersect_wall.extend(wall_intersects_west)

    window_east, \
    wall_east, \
    normals_windows_east, \
    normals_walls_east, \
    wall_intersects_east = calc_windows_walls(facade_list_east, wwr_east, potentially_intersecting_solids)
    if len(window_east) != 0:
        window_list.extend(window_east)
        orientation_win.extend(['east'] * len(window_east))
        normals_win.extend(normals_windows_east)
    wall_list.extend(wall_east)
    orientation.extend(['east'] * len(wall_east))
    normals_walls.extend(normals_walls_east)
    intersect_wall.extend(wall_intersects_east)

    window_north, \
    wall_north, \
    normals_windows_north, \
    normals_walls_north, \
    wall_intersects_north = calc_windows_walls(facade_list_north, wwr_north, potentially_intersecting_solids)
    if len(window_north) != 0:
        window_list.extend(window_north)
        orientation_win.extend(['north'] * len(window_north))
        normals_win.extend(normals_windows_north)
    wall_list.extend(wall_north)
    orientation.extend(['north'] * len(wall_north))
    normals_walls.extend(normals_walls_north)
    intersect_wall.extend(wall_intersects_north)

    window_south, \
    wall_south, \
    normals_windows_south, \
    normals_walls_south, \
    wall_intersects_south = calc_windows_walls(facade_list_south, wwr_south, potentially_intersecting_solids)
    if len(window_south) != 0:
        window_list.extend(window_south)
        orientation_win.extend(['south'] * len(window_south))
        normals_win.extend(normals_windows_south)
    wall_list.extend(wall_south)
    orientation.extend(['south'] * len(wall_south))
    normals_walls.extend(normals_walls_south)
    intersect_wall.extend(wall_intersects_south)

    geometry_3D_zone = {"name": name, "windows": window_list, "walls": wall_list, "roofs": roof_list,
                        "footprint": footprint_list, "orientation_walls": orientation,
                        "orientation_windows": orientation_win,
                        "normals_windows": normals_win, "normals_walls": normals_walls,
                        "intersect_walls": intersect_wall}

    building_geometry = BuildingGeometry(**geometry_3D_zone, terrain_elevation=elevation)
    building_geometry.save(os.path.join(geometry_pickle_dir, 'zone', str(name)))
    return name


def burn_buildings(geometry, elevation_map, tolerance):
    if geometry.has_z:
        # remove elevation - we'll add it back later by intersecting with the topography
        point_list_2D = ((a, b) for (a, b, _) in geometry.exterior.coords)
    else:
        point_list_2D = geometry.exterior.coords
    point_list_3D = [(a, b, 0) for (a, b) in point_list_2D]  # add 0 elevation

    # creating floor surface in pythonocc
    face = construct.make_polygon(point_list_3D)
    # get the midpt of the face
    face_midpt = calculate.face_midpt(face)

    terrain_tin = elevation_map.generate_tin(tolerance)
    # make shell out of tin_occface_list and create OCC object
    terrain_shell = construct.make_shell(terrain_tin)

    # project the face_midpt to the terrain and get the elevation
    inter_pt, inter_face = calc_intersection(terrain_shell, face_midpt, (0, 0, 1), tolerance)

    # reconstruct the footprint with the elevation
    loc_pt = (inter_pt.X(), inter_pt.Y(), inter_pt.Z())
    face = fetch.topo2topotype(modify.move(face_midpt, loc_pt, face))
    return face, inter_pt.Z()


def calc_solid(face_footprint, range_floors, floor_to_floor_height):
    # create faces for every floor and extrude the solid

    def cal_face_list(floor_counter):
        dist2mve = floor_counter * floor_to_floor_height
        # get midpt of face
        orig_pt = calculate.face_midpt(face_footprint)
        # move the pt 1 level up
        dest_pt = modify.move_pt(orig_pt, (0, 0, 1), dist2mve)
        moved_face = modify.move(orig_pt, dest_pt, face_footprint)

        return moved_face

    moved_face_list = np.vectorize(cal_face_list)(range_floors)
    # make checks to satisfy a closed geometry also called a shell

    vertical_shell = construct.make_loft(moved_face_list)
    vertical_face_list = fetch.topo_explorer(vertical_shell, "face")
    roof = moved_face_list[-1]
    footprint = moved_face_list[0]
    all_faces = []
    all_faces.append(footprint)
    all_faces.extend(vertical_face_list)
    all_faces.append(roof)
    building_shell_list = construct.sew_faces(all_faces)

    # make sure all the normals are correct (they are pointing out)
    bldg_solid = construct.make_solid(building_shell_list[0])
    bldg_solid = modify.fix_close_solid(bldg_solid)
    #
    # if config.general.debug:
    #     # visualize building progress while debugging
    #     face_list = fetch.topo_explorer(bldg_solid, "face")
    #     edges = calculate.face_normal_as_edges(face_list,5)
    #     utility.visualise([face_list,edges],["WHITE","BLACK"])
    return bldg_solid


class Points(object):
    def __init__(self, point_to_evaluate):
        self.point_to_evaluate = point_to_evaluate


def calc_windows_walls(facade_list, wwr, potentially_intersecting_solids):
    window_list = []
    wall_list = []
    normals_win = []
    normals_wall = []
    wall_intersects = []
    number_intersecting_solids = len(potentially_intersecting_solids)
    for surface_facade in facade_list:
        # get coordinates of surface
        ref_pypt = calculate.face_midpt(surface_facade)
        standard_normal = calculate.face_normal(surface_facade)  # to avoid problems with fuzzy normals

        # evaluate if the surface intersects any other solid (important to erase non-active surfaces in the building
        # simulation model)
        data_point = Points(modify.move_pt(ref_pypt, standard_normal, 0.1))

        if number_intersecting_solids:
            # flag weather it intersects a surrounding geometry
            intersects = np.vectorize(calc_intersection_face_solid)(potentially_intersecting_solids, data_point)
            intersects = sum(intersects)
        else:
            intersects = 0

        if intersects > 0:  # the face intersects so it is a wall
            wall_list.append(surface_facade)
            normals_wall.append(standard_normal)
            wall_intersects.append(1)
        else:
            try:    # Ensure wwr is a float
                wwr = float(wwr)
            except ValueError:
                raise ValueError(f"Invalid value for wwr: {wwr}. It must be a numeric value.")

            # offset the facade to create a window according to the wwr
            if 0.0 < wwr < 1.0:
                # for window
                window = create_windows(surface_facade, wwr, ref_pypt)
                window_list.append(window)
                normals_win.append(standard_normal)
                # for walls
                hollowed_facade, hole_facade = create_hollowed_facade(surface_facade,
                                                                      window)  # accounts for hole created by window
                wall_intersects.extend([intersects] * len(hollowed_facade))
                wall_list.extend(hollowed_facade)
                normals_wall.extend([standard_normal] * len(hollowed_facade))

            elif wwr == 1.0:
                window_list.append(surface_facade)
                normals_win.append(standard_normal)
            else:
                wall_list.append(surface_facade)
                normals_wall.append(standard_normal)
                wall_intersects.append(intersects)

    return window_list, wall_list, normals_win, normals_wall, wall_intersects


def calc_intersection_face_solid(potentially_intersecting_solid, point):
    with cea.utilities.devnull():
        point_in_solid = calculate.point_in_solid(point.point_to_evaluate, potentially_intersecting_solid)
    if point_in_solid:
        intersects = 1
    else:
        intersects = 0
    return intersects


class ElevationMap(object):
    __slots__ = ['elevation_map', 'x_coords', 'y_coords', 'x_size', 'y_size', 'nodata']

    def __init__(self, elevation_map, x_coords, y_coords, x_size, y_size, nodata=None):
        self.elevation_map = elevation_map
        self.x_coords = x_coords
        self.y_coords = y_coords

        self.x_size = x_size
        self.y_size = y_size

        self.nodata = nodata

    @classmethod
    def read_raster(cls, raster):
        band = raster.GetRasterBand(1)
        nodata = band.GetNoDataValue()

        a = band.ReadAsArray()

        y, x = np.shape(a)
        upper_left_x, x_size, x_rotation, upper_left_y, y_rotation, y_size = raster.GetGeoTransform()

        if x_rotation != 0 or y_rotation != 0:
            raise ValueError("Rotation in raster is not supported.")

        x_coords = np.arange(start=0, stop=x) * x_size + upper_left_x + (x_size / 2)  # add half the cell size
        y_coords = np.arange(start=0, stop=y) * y_size + upper_left_y + (y_size / 2)  # to centre the point

        return cls(a, x_coords, y_coords, x_size, y_size, nodata)

    def get_elevation_map_from_geometry(self, geometry, extra_points=3):
        minx, miny, maxx, maxy = geometry.bounds

        # Ensure geometry bounds is within elevation map
        if (minx < self.x_coords[0] - self.x_size or maxx > self.x_coords[-1] + self.x_size
                or miny < self.y_coords[-1] + self.y_size or maxy > self.y_coords[0] - self.y_size):
            raise ValueError("Geometry bounds not within the elevation map.")

        x_start = np.searchsorted(self.x_coords - self.x_size, minx, side='left') - 1
        x_end = np.searchsorted(self.x_coords + self.x_size, maxx, side='right')
        y_start = len(self.y_coords) - np.searchsorted((self.y_coords - self.y_size)[::-1], maxy, side='left') - 1
        y_end = len(self.y_coords) - np.searchsorted((self.y_coords + self.y_size)[::-1], miny, side='right')

        # Consider extra points
        x_start = max(x_start - extra_points, 0)
        x_end = min(x_end + extra_points, len(self.x_coords))
        y_start = max(y_start - extra_points, 0)
        y_end = min(y_end + extra_points, len(self.y_coords))

        new_elevation_map = self.elevation_map[y_start:y_end + 1, x_start:x_end + 1]
        new_x_coords = self.x_coords[x_start:x_end + 1]
        new_y_coords = self.y_coords[y_start:y_end + 1]

        return ElevationMap(new_elevation_map, new_x_coords, new_y_coords, self.x_size, self.y_size, self.nodata)

    def generate_tin(self, tolerance=1e-6):
        # Ignore no data values from raster
        y_index, x_index = np.nonzero(self.elevation_map != self.nodata)
        _x_coords = self.x_coords[x_index]
        _y_coords = self.y_coords[y_index]

        raster_points = ((x, y, z) for x, y, z in zip(_x_coords, _y_coords, self.elevation_map[y_index, x_index]))

        tin_occface_list = construct.delaunay3d(raster_points, tolerance=tolerance)

        return tin_occface_list


def standardize_coordinate_systems(zone_df, surroundings_df, trees_df, terrain_raster):
    # Change all to projected cr (to meters)
    lat, lon = get_lat_lon_projected_shapefile(zone_df)
    crs = get_projected_coordinate_system(lat, lon)

    reprojected_zone_df = zone_df.to_crs(crs)
    reprojected_surroundings_df = surroundings_df.to_crs(crs)
    reprojected_trees_df = trees_df.to_crs(crs)

    reprojected_terrain = gdal.Warp(
        '',  # Empty string as the output file path means in-memory
        terrain_raster,
        format='VRT',  # Use VRT format for in-memory operation
        dstSRS=crs
    )

    print(f"Reprojected scene to `EPSG:{crs_to_epsg(crs)}`")
    return reprojected_zone_df, reprojected_surroundings_df, reprojected_trees_df, reprojected_terrain


def check_terrain_bounds(zone_df, surroundings_df, trees_df, terrain_raster):
    total_df = pd.concat([zone_df, surroundings_df, trees_df])

    # minx, miny, maxx, maxy
    geometry_bounds = total_df.total_bounds

    upper_left_x, x_size, x_rotation, upper_left_y, y_rotation, y_size = terrain_raster.GetGeoTransform()
    minx = upper_left_x
    maxy = upper_left_y
    maxx = minx + x_size * terrain_raster.RasterXSize
    miny = maxy + y_size * terrain_raster.RasterYSize

    if minx > geometry_bounds[0] or miny > geometry_bounds[1] or maxx < geometry_bounds[2] or maxy < geometry_bounds[3]:
        raise ValueError('Terrain provided does not cover all geometries. '
                         'Bounds of terrain must be larger than the total bounds of the scene.')


def tree_geometry_generator(tree_df, terrain_raster):
    terrian_projection = terrain_raster.GetProjection()
    proj4_str = osr.SpatialReference(wkt=terrian_projection).ExportToProj4()
    tree_df = tree_df.to_crs(proj4_str)

    elevation_map = ElevationMap.read_raster(terrain_raster)

    from multiprocessing.pool import Pool
    from multiprocessing import cpu_count

    with Pool(cpu_count() - 1) as pool:
        surfaces = [
            fetch.faces_frm_solid(solid) for (solid, _) in pool.starmap(
                process_geometries, (
                    (geom, elevation_map, (0, 1), z) for geom, z in zip(tree_df['geometry'], tree_df['height_tc'])
                )
            )
        ]

    return surfaces


def geometry_main(config, zone_df, surroundings_df, trees_df, terrain_raster, architecture_wwr_df, geometry_pickle_dir):
    print("Standardizing coordinate systems")
    zone_df, surroundings_df, trees_df, terrain_raster = standardize_coordinate_systems(
        zone_df, surroundings_df, trees_df, terrain_raster)

    # clear in case there are repeated buildings from zone in surroundings file
    filter_surrounding_buildings = ~surroundings_df["name"].isin(zone_df["name"])
    surroundings_df = surroundings_df[filter_surrounding_buildings]

    check_terrain_bounds(zone_df, surroundings_df, trees_df, terrain_raster)

    # Create a triangulated irregular network of terrain from raster
    print("Reading terrain geometry")
    elevation_map = ElevationMap.read_raster(terrain_raster)
    terrain_tin = elevation_map.generate_tin()

    # transform buildings 2D to 3D and add windows
    print("Creating 3D building surfaces")
    os.makedirs(geometry_pickle_dir, exist_ok=True)
    geometry_3D_zone, geometry_3D_surroundings = building_2d_to_3d(zone_df, surroundings_df, architecture_wwr_df,
                                                                   elevation_map, config, geometry_pickle_dir)

    tree_surfaces = []
    if len(trees_df.geometry) > 0:
        print("Creating tree surfaces")
        tree_surfaces = tree_geometry_generator(trees_df, terrain_raster)

    return terrain_tin, geometry_3D_zone, geometry_3D_surroundings, tree_surfaces


if __name__ == '__main__':
    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    settings = config.radiation

    # run routine City GML LOD 1
    time1 = time.time()
    geometry_terrain, geometry_3D_zone, geometry_3D_surroundings = geometry_main(locator, config)

    # to visualize the results
    geometry_buildings = []
    geometry_buildings_nonop = []
    walls_intercept = [val for sublist in geometry_3D_zone for val, inter in
                       zip(sublist['walls'], sublist['intersect_walls']) if inter > 0]
    windows = [val for sublist in geometry_3D_zone for val in sublist['windows']]
    walls = [val for sublist in geometry_3D_zone for val in sublist['walls']]
    roofs = [val for sublist in geometry_3D_zone for val in sublist['roofs']]
    footprint = [val for sublist in geometry_3D_zone for val in sublist['footprint']]
    walls_s = [val for sublist in geometry_3D_surroundings for val in sublist['walls']]
    windows_s = [val for sublist in geometry_3D_surroundings for val in sublist['windows']]
    roof_s = [val for sublist in geometry_3D_surroundings for val in sublist['roofs']]

    geometry_buildings_nonop.extend(windows)
    geometry_buildings_nonop.extend(windows_s)
    geometry_buildings.extend(walls)
    geometry_buildings.extend(roofs)
    geometry_buildings.extend(footprint)
    geometry_buildings.extend(walls_s)
    geometry_buildings.extend(roof_s)
    normals_terrain = calculate.face_normal_as_edges(geometry_terrain, 5)
    utility.visualise([geometry_terrain, geometry_buildings, geometry_buildings_nonop, walls_intercept],
                      ["GREEN", "WHITE", "BLUE", "RED"])  # install Wxpython

    utility.visualise([walls_intercept],
                      ["RED"])

    utility.visualise([walls],
                      ["RED"])

    utility.visualise([windows],
                      ["RED"])
