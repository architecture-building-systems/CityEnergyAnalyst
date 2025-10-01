"""
Geometry generator from
Shapefiles (building footprint)
and .tiff (terrain)

into 3D geometry with windows and roof equivalent to LOD3

"""

from __future__ import annotations

import math
import os
import time
from itertools import repeat
from typing import TYPE_CHECKING, Literal

import numpy as np
import pandas as pd
from compas.datastructures import Mesh
from compas.geometry import (
    Point,
    Polygon,
    Vector,
    intersection_ray_mesh,
)
from compas_occ.brep import OCCBrep
from OCC.Core.BRepClass3d import BRepClass3d_SolidClassifier
from OCC.Core.gp import gp_Pnt
from OCC.Core.TopAbs import TopAbs_IN
from osgeo import gdal, osr

import cea
import cea.config
import cea.inputlocator
import cea.utilities.parallel
from cea.resources.radiation.building_geometry_radiation import (
    BuildingGeometryForRadiation,
)

if TYPE_CHECKING:
    import geopandas as gpd
    import shapely
    from compas.geometry import Line

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Kian Wee Chen"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

from cea.utilities.standardize_coordinates import (
    crs_to_epsg,
    get_lat_lon_projected_shapefile,
    get_projected_coordinate_system,
)


def identify_surfaces_type(
    face_list: list[Polygon],
) -> tuple[
    list[Polygon],
    list[Polygon],
    list[Polygon],
    list[Polygon],
    list[Polygon],
    list[Polygon],
]:
    roof_list = []
    footprint_list = []
    facade_list_north = []
    facade_list_west = []
    facade_list_east = []
    facade_list_south = []
    vec_vertical = Vector(0, 0, 1)
    vec_horizontal = Vector(0, 1, 0)

    # distinguishing between facade, roof and footprint.
    for f in face_list:
        # get the normal of each face
        n = f.normal
        angle_to_vertical = vec_vertical.angle(n, degrees=True)
        # means its a facade
        if angle_to_vertical > 45 and angle_to_vertical < 135:
            flatten_n = n.copy()
            flatten_n.z = (
                0  # need to flatten to erase Z just to consider vertical surfaces.
            )
            angle_to_horizontal = vec_horizontal.angle(flatten_n, degrees=True)
            if (0 <= angle_to_horizontal <= 45) or (315 <= angle_to_horizontal <= 360):
                facade_list_north.append(f)
            elif 45 < angle_to_horizontal < 135:
                facade_list_west.append(f)
            elif 135 <= angle_to_horizontal <= 225:
                facade_list_south.append(f)
            elif 225 < angle_to_horizontal < 315:
                facade_list_east.append(f)
        elif angle_to_vertical <= 45:
            roof_list.append(f)
        elif angle_to_vertical >= 135:
            footprint_list.append(f)

    return (
        facade_list_north,
        facade_list_west,
        facade_list_east,
        facade_list_south,
        roof_list,
        footprint_list,
    )


def calc_intersection(
    surface: Mesh, point: Point, direction: Vector
) -> tuple[int, Point]:
    """This script calculates the intersection of a ray from a particular point to the terrain.

    :param surface: the terrain mesh to be intersected.
    :type surface: Mesh
    :param edges_coords: the coordinates of the point from which the ray is cast.
    :type edges_coords: Point
    :param edges_dir: the direction of the ray, which is usually a vector pointing upwards.
    :type edges_dir: Vector
    :return: a tuple containing the index of the face that was hit and the intersection point.
        if no intersection was found, it returns (None, None).
    :rtype: tuple[int | None, Point | None]
    """
    ray = (point, direction)
    hits: list[tuple[int, float, float, float]] = intersection_ray_mesh(ray, surface.to_vertices_and_faces())
    # idx_face: int, u: float, v: float, t: float = hits[0] if hits else (None, None, None, None)
    if hits:
        idx_face, u, v, t = hits[0]
    # u, v are the barycentric coordinates of the intersection point on the face.
        face_points = surface.face_points(idx_face)
        w = 1 - u - v
        p0 = face_points[0]
        p1 = face_points[1]
        p2 = face_points[2]
        inter_pt = point.copy()
        inter_pt.z = p0.z * w + p1.z * v + p2.z * u
        return idx_face, inter_pt
    else:
        raise ValueError("No intersection found between the ray and the surface mesh.")

def create_windows(surface: Polygon, 
                   wwr: float, 
                   ) -> tuple[Polygon, list[Polygon]]:
    """
    This function creates a window by schrinking the surface according to the wwr around the reference point.
    The generated window has the same shape as the original surface.
    Each side of the surface is shrunk by `sqrt(wwr)`, so that the area is scaled down to `wwr * A_surface`.

    :param surface: the surface to be shrunk.
    :type surface: OCCface
    :param wwr: Window-to-Wall Ratio: the ratio of the surface that will be a window, ranges from 0 to 1.
    :type wwr: float
    :param ref_pypt: the reference point for the scaling operation. Usually the center point of the surface.
    :type ref_pypt: tuple
    :return: the scaled surface which represents the window.
    :rtype: OCCface
    """
    # scaler = math.sqrt(wwr)
    # return fetch.topo2topotype(modify.uniform_scale(surface, scaler, scaler, scaler, ref_pypt))
    window: Polygon = surface.scaled(math.sqrt(wwr))
    window.translate(Vector.from_start_end(window.centroid, surface.centroid))
    hollowed_surfaces: list[Polygon] = []
    for i, line_window in enumerate(window.lines):
        line_surface = surface.lines[i]
        wall_trapezoid = Polygon([line_surface.start, line_surface.end, line_window.end, line_window.start])
        hollowed_surfaces.append(wall_trapezoid)
    return window, hollowed_surfaces

def calc_building_solids(buildings_df: gpd.GeoDataFrame, 
                         geometry_simplification: float, 
                         elevation_map: ElevationMap, 
                         num_processes: int,
                         ) -> tuple[list[OCCBrep], list[float]]:
    """create building solids respecting their elevation, from building GeoDataFrame and elevation map.

    :param buildings_df: either the zone or surroundings buildings dataframe. 
        It should be read from either `"\\scenario\\inputs\\building-geometry\\zone.shp"` 
        or `"\\scenario\\inputs\\building-geometry\\surroundings.shp"`, 
        and the index of this GeoDataFrame should be the building names.
    :type buildings_df: GeoDataFrame
    :param geometry_simplification: the tolerance of simplification. 
        "All parts of a simplified geometry will be no more than tolerance distance from the original." 
        (from `geopandas.GeoSeries.simplify`)
    :type geometry_simplification: float
    :param elevation_map: an instance of `ElevationMap` that contains the terrain elevation data, read from a raster file 
    `"\\scenario\\inputs\\topography\\terrain.tif"`.
    :type elevation_map: ElevationMap
    :param num_processes: number of processes to use for parallel computation.
    :type num_processes: int
    :return: a list of solids representing the building external shells, each made from footprint + vertical external walls + roof.
    :rtype: list[OCCsolid]
    :return: a list of elevations corresponding to each building solid, where each elevation is a float value.
    :rtype: list[float]
    """

    # simplify geometry for buildings of interest
    geometries = buildings_df.geometry.simplify(geometry_simplification, preserve_topology=True)

    height = buildings_df['height_ag'].astype(float)
    nfloors = buildings_df['floors_ag'].astype(int)
    void_decks = buildings_df['void_deck'].astype(int)
    if not all(void_decks <= nfloors):
        raise ValueError(f"Void deck values must be less than or equal to the number of floors for each building. "
                         f"Found void_deck values: {void_decks.values} and number of floors: {nfloors.values}.")
    
    range_floors = [range(void_deck, floors + 1) for void_deck, floors in zip(void_decks, nfloors)]
    floor_to_floor_height = height / nfloors

    n = len(geometries)
    out: list[tuple[OCCBrep, float]] = cea.utilities.parallel.vectorize(process_geometries, num_processes,
                                           on_complete=print_terrain_intersection_progress)(
        geometries, repeat(elevation_map, n), range_floors, floor_to_floor_height)

    solids, elevations = zip(*out)
    return list(solids), list(elevations)

def process_geometries(geometry: shapely.Polygon, 
                       elevation_map: ElevationMap, 
                       range_floors: range, 
                       floor_to_floor_height: float,
                       ) -> tuple[OCCBrep, float]:
    """
    gets the 2D geometry as well as the height and number of floors, and returns a solid representing the building. 
    Also returns the elevation of the building footprint using elevation_map.

    :param geometry: one building geometry from the buildings GeoDataFrame.
    :type geometry: shapely.Polygon
    :param elevation_map: the elevation map for the whole site.
    :type elevation_map: ElevationMap
    :param range_floors: range of floors for the building. For example, a building of 3 floors will have `range(4) = [0, 1, 2, 3]`.
    :type range_floors: range
    :param floor_to_floor_height: the height of each level of the building. 
    :type floor_to_floor_height: float
    :return: a solid representing the building, made from footprint + vertical external walls + roof.
    :rtype: OCCsolid
    :return: the elevation of the terrain at the footprint of the building.
    :rtype: float
    """
    elevation_map_for_geometry = elevation_map.get_elevation_map_from_geometry(geometry)
    # burn buildings footprint into the terrain and return the location of the new face
    face_footprint, elevation = burn_buildings(geometry, elevation_map_for_geometry, 1e-12)
    # create floors and form a solid
    building_solid = calc_solid(face_footprint, range_floors, floor_to_floor_height)

    return building_solid, elevation


def calc_building_geometry_surroundings(name: str, 
                                        building_solid: OCCBrep, 
                                        geometry_pickle_dir: str,
                                        ) -> str:
    (
        facade_list_north,
        facade_list_west,
        facade_list_east,
        facade_list_south,
        roof_list,
        footprint_list,
    ) = identify_surfaces_type([face.to_polygon() for face in building_solid.faces])
    facade_list = facade_list_north + facade_list_west + facade_list_east + facade_list_south
    geometry_3D_surroundings = {
        "name": name,
        "walls": facade_list,
        "roofs": roof_list,
        "footprint": footprint_list,
    }

    building_geometry = BuildingGeometryForRadiation.from_dict(geometry_3D_surroundings)
    building_geometry.save(os.path.join(geometry_pickle_dir, 'surroundings', str(name)))
    return name


def building_2d_to_3d(zone_df: gpd.GeoDataFrame, 
                      surroundings_df: gpd.GeoDataFrame, 
                      architecture_wwr_df: pd.DataFrame, 
                      elevation_map: ElevationMap, 
                      config: cea.config.Configuration, 
                      geometry_pickle_dir: str
                      ) -> tuple[list[str], list[str]]:
    """reconstruct 3D building geometries with windows and store each building's 3D data into a file.

    :param zone_df: data and 2D geometry of all analyzed building in the site, typically read from `zone.shp`.
    :type zone_df: GeoDataFrame
    :param surroundings_df: data and 2D geometry of surrounding buildings.
    :type surroundings_df: GeoDataFrame
    :param architecture_wwr_df: building envelope data.
    :type architecture_wwr_df: DataFrame
    :param elevation_map: 3D elevation map of the site.
    :type elevation_map: ElevationMap
    :param config: Configuration object with the settings (general and radiation)
    :type config: cea.config.Configuration
    :param geometry_pickle_dir: directory for saving building's 3D data.
    :type geometry_pickle_dir: str
    :return: names of analyzed buildings.
    :rtype: list[str]
    :return: names of surrounding buildings.
    :rtype: list[str]

    .. note::

        the function will not return any useful data, but it stores the reconstructed 
        building geometry (including envelopes, windows, their orientation 
        and if they are intersected with other solids) into a file that could be used in other steps.
    """
    # Config variables
    num_processes: int = config.get_number_of_processes()
    zone_simplification: float = config.radiation.zone_geometry # type: ignore
    surroundings_simplification: float = config.radiation.surrounding_geometry # type: ignore
    neglect_adjacent_buildings: bool = config.radiation.neglect_adjacent_buildings # type: ignore

    print('Calculating terrain intersection of building geometries')
    zone_buildings_df: pd.DataFrame = zone_df.set_index('name')
    # merge architecture wwr data into zone buildings dataframe with "name" column,
    # because we want to use void_deck when creating the building solid.
    zone_building_names = zone_buildings_df.index.values
    zone_building_solid_list, zone_elevations = calc_building_solids(zone_buildings_df, zone_simplification,
                                                                     elevation_map, num_processes)

    # Check if there are any buildings in surroundings_df before processing
    if not surroundings_df.empty:
        surroundings_buildings_df = surroundings_df.set_index('name')
        if 'void_deck' not in surroundings_buildings_df.columns:
            surroundings_buildings_df['void_deck'] = 0
            
        surroundings_building_names = surroundings_buildings_df.index.values
        surroundings_building_solid_list, _ = calc_building_solids(
            surroundings_buildings_df, surroundings_simplification, elevation_map, num_processes)
        # calculate geometry for the surroundings
        print('Generating geometry for surrounding buildings')
        geometry_3D_surroundings = [calc_building_geometry_surroundings(x, y, geometry_pickle_dir) for x, y in
                                    zip(surroundings_building_names, surroundings_building_solid_list)]
    else:
        surroundings_building_solid_list = []
        geometry_3D_surroundings = []

    # calculate geometry for the zone of analysis
    print('Generating geometry for buildings in the zone of analysis')
    n = len(zone_building_names)
    calc_zone_geometry_multiprocessing = cea.utilities.parallel.vectorize(calc_building_geometry_zone,
                                                                          num_processes,
                                                                          on_complete=print_progress)

    if not neglect_adjacent_buildings:
        all_building_solid_list = zone_building_solid_list + surroundings_building_solid_list
    else:
        all_building_solid_list = []
    # TODO: maybe move calc_building_solid into this function and avoid using archiecture_wwr_df, because it's already merged into zone_buildings_df.
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
    print("Creating geometry for building {i} completed out of {n}".format(i=i + 1, n=n))


def are_buildings_close_to_eachother(x_1, y_1, solid2: OCCBrep, dist=100):
    pmin, pmax = brep_bounding_box(solid2)
    x_2 = pmin.x
    y_2 = pmin.y
    delta = math.sqrt((y_2 - y_1) ** 2 + (x_2 - x_1) ** 2)
    if delta <= dist:
        return True
    else:
        return False

def brep_bounding_box(brep: OCCBrep) -> tuple[Point, Point]:
    """Get the axis-aligned bounding box of a brep."""
    points = brep.points
    xs = [p.x for p in points]
    ys = [p.y for p in points]
    zs = [p.z for p in points]
    min_point = Point(min(xs), min(ys), min(zs))
    max_point = Point(max(xs), max(ys), max(zs))
    return min_point, max_point

def calc_building_geometry_zone(name: str, 
                                building_solid: OCCBrep, 
                                all_building_solid_list: list[OCCBrep], 
                                architecture_wwr_df: gpd.GeoDataFrame,
                                geometry_pickle_dir: str, 
                                neglect_adjacent_buildings: bool, 
                                elevation: float,
                                ) -> str:
    """
    calculates the 3D geometry of a building, including its windows and walls,
    and saves the geometry into a file.

    :param name: name of building.
    :type name: str
    :param building_solid: 
        a closed geometry representing the building external shells, 
        made from footprint + vertical external walls + roof (without windows).
    :type building_solid: OCCsolid
    :param all_building_solid_list: a list of all_building_solid_list, or an empty list if `neglect_adjacent_buildings == True`.
    :type all_building_solid_list: list[OCCsolid]
    :param architecture_wwr_df: a dataframe read from `locator.get_building_architecture` containing envelope info.
    :type architecture_wwr_df: DataFrame
    :param geometry_pickle_dir: folder path to save the created `BuildingGeometryForRadiation` object.
    :type geometry_pickle_dir: str
    :param neglect_adjacent_buildings: True if no adjacency of other buildings is considered.
    :type neglect_adjacent_buildings: bool
    :param elevation: elevation of building footprint's middle point.
    :type elevation: float
    :return: name of building.
    :rtype: str

    .. note::

        the function will not return any useful data, but it stores the reconstructed 
        building geometry (including envelopes, windows, their orientation 
        and if they are intersected with other solids) into a file that could be used in other steps.
    """
    # now get all surfaces and create windows only if the buildings are in the area of study
    window_list: list[Polygon] = []
    wall_list: list[Polygon] = []
    orientation: list[str] = []
    orientation_win: list[str] = []
    normals_walls: list[Vector] = []
    normals_win: list[Vector] = []
    intersect_wall: list[Literal[0, 1]] = []

    # check if buildings are close together and it merits to check the intersection
    # close together is defined as:
    # if two building bounding boxes' southwest corner are smaller than 100m on their xy-plane projection (ignoring z-axis).
    # TODO: maybe also check if one building's top roof is within another building's volume when two buildings are stacked.
    potentially_intersecting_solids = []
    if not neglect_adjacent_buildings:
        pmin, pmax = brep_bounding_box(building_solid)
        for solid in all_building_solid_list:
            if are_buildings_close_to_eachother(pmin.x, pmin.y, solid):
                potentially_intersecting_solids.append(solid)

    # identify building surfaces according to angle:
    face_list = [face.to_polygon() for face in building_solid.faces]
    facade_list_north, facade_list_west, \
    facade_list_east, facade_list_south, roof_list, footprint_list = identify_surfaces_type(face_list)

    # get window properties
    def safe_float(val):
        # Convert numpy scalar or complex to float, raise error if complex part is nonzero
        if hasattr(val, 'real'):
            if getattr(val, 'imag', 0) != 0:
                raise ValueError(f"Cannot convert complex value {val} to float.")
            return float(val.real)
        return float(val)

    wwr_west = safe_float(architecture_wwr_df.loc[name, "wwr_west"])
    wwr_east = safe_float(architecture_wwr_df.loc[name, "wwr_east"])
    wwr_north = safe_float(architecture_wwr_df.loc[name, "wwr_north"])
    wwr_south = safe_float(architecture_wwr_df.loc[name, "wwr_south"])

    def process_facade(facade_list: list[Polygon], wwr: float, orientation_label: str):
        window, wall, normals_window, normals_wall, wall_intersects = calc_windows_walls(
            facade_list, wwr, potentially_intersecting_solids)
        if len(window) != 0:
            window_list.extend(window)
            orientation_win.extend([orientation_label] * len(window))
            normals_win.extend(normals_window)
        wall_list.extend(wall)
        orientation.extend([orientation_label] * len(wall))
        normals_walls.extend(normals_wall)
        intersect_wall.extend(wall_intersects)

    process_facade(facade_list_west, wwr_west, 'west')
    process_facade(facade_list_east, wwr_east, 'east')
    process_facade(facade_list_north, wwr_north, 'north')
    process_facade(facade_list_south, wwr_south, 'south')

    intersect_windows = [0] * len(window_list)

    _, _, _, normals_roof, intersect_roof = calc_windows_walls(roof_list, 0.0, potentially_intersecting_solids)
    orientation_roofs = ["top"] * len(roof_list)

    _, _, _, normals_footprint, intersect_footprint = calc_windows_walls(footprint_list, 0.0, potentially_intersecting_solids)
    orientation_footprint = ["bottom"] * len(footprint_list)

    geometry_3D_zone = {"name": name, "footprint": footprint_list, "terrain_elevation": elevation,
                        "windows": window_list,       "orientation_windows": orientation_win,          "normals_windows": normals_win,          "intersect_windows": intersect_windows,
                        "walls": wall_list,           "orientation_walls": orientation,                "normals_walls": normals_walls,          "intersect_walls": intersect_wall,
                        "roofs": roof_list,           "orientation_roofs": orientation_roofs,          "normals_roofs": normals_roof,           "intersect_roofs": intersect_roof,
                        "undersides": footprint_list, "orientation_undersides": orientation_footprint, "normals_undersides": normals_footprint, "intersect_undersides": intersect_footprint, 
                        }
    # see class BuildingGeometryForRadiation for the difference between footprint and undersides.

    building_geometry = BuildingGeometryForRadiation.from_dict(geometry_3D_zone)
    building_geometry.save(os.path.join(geometry_pickle_dir, 'zone', str(name)))
    return name


def burn_buildings(geometry: shapely.Polygon, 
                   elevation_map: ElevationMap, 
                   tolerance: float,
                   ) -> tuple[Polygon, float]:
    """find the elevation of building footprint polygon by intersecting the center point of the polygon 
    with the terrain elevation map, then move the polygon to that elevation.

    :param geometry: a polygon representing the building footprint.
    :type geometry: shapely.Polygon
    :param elevation_map: elevation map that contains the building footprint polygon.
    :type elevation_map: ElevationMap
    :param tolerance: The minimal surface area of each triangulated face. Any faces smaller than the tolerance will be deleted.
    :type tolerance: float
    :return: the bottom surface of the building.
    :rtype: Polygon
    :return: the elevation of the terrain at the footprint of the building.
    :rtype: float
    """
    if geometry.has_z:
        point_list_2D = ((a, b) for (a, b, _) in geometry.exterior.coords)
    else:
        point_list_2D = geometry.exterior.coords

    terrain_tin = elevation_map.generate_tin(tolerance)
    point_list_3D = [[a, b, 0] for (a, b) in point_list_2D]  # add 0 elevation
    footprint_polygon = Polygon(point_list_3D)
    footprint_midpt = footprint_polygon.centroid
    proj_vector = Vector(0, 0, 1)  # project upwards
    _, inter_pt = calc_intersection(terrain_tin, footprint_midpt, proj_vector)
    move_vector = Vector(0, 0, inter_pt.z)
    footprint_polygon.translate(move_vector)
    return footprint_polygon, inter_pt.z


def calc_solid(face_footprint: Polygon, 
               range_floors: range, 
               floor_to_floor_height: float,
               ) -> OCCBrep:
    """
    extrudes the footprint surface into a 3D solid.

    :param face_footprint: footprint of the building. 
    :type face_footprint: Polygon
    :param range_floors: 
        range of floors for the building. 
        For example, a building of 3 floors will have `range(4) = [0, 1, 2, 3]`, 
        because it has 4 floors (1 ground floor + 2 internal ceilings + 1 roof).
    :type range_floors: range
    :param floor_to_floor_height: the height of each level of the building.
        For example, if the building has 3 floors and a height of 9m, then `floor_to_floor_height = 9 / 3 = 3`.
    :type floor_to_floor_height: float
    :return: a solid representing the building, made from footprint + vertical external walls + roof.
    :rtype: list[Brep]
    """
    building_breps: list[OCCBrep] = []
    for i_floor in range_floors:
        move_vector = Vector(0, 0, i_floor * floor_to_floor_height)
        slab: Polygon = face_footprint.translated(move_vector)
        walls = from_floor_extrude_walls(slab, floor_to_floor_height)
        ceiling = slab.translated(Vector(0, 0, floor_to_floor_height))
        building_breps.append(OCCBrep.from_polygons([slab] + walls + [ceiling]))
    building_brep = building_breps[0].boolean_union(*building_breps[1:])
    return building_brep

def extrude_line_to_polygon(line: Line, height: float, direction: Vector = Vector(0, 0, 1)) -> Polygon:
    """Make a rectangular wall polygon by extruding a line along a direction."""
    v = direction.unitized().scaled(height)
    return Polygon([line.start, line.end, line.end.translated(v), line.start.translated(v)])

def from_floor_extrude_walls(floor: Polygon, height: float) -> list[Polygon]:
    """reads the floor polygon and create vertical walls from each of its edges.


    :param floor: a polygon on XY plane representing the bottom surface of the building floor.
    :type floor: Polygon
    :param height: the height of the building floor, which is the height of the extruded vertical walls.
    :type height: float
    :return: a list of vertically extruded polygons representing the walls of the building floor.
    :rtype: list[Polygon]
    """
    if not isinstance(floor, Polygon):
        raise TypeError(f"Expected floor to be a Polygon, got {type(floor)} instead.")
    if height <= 0:
        raise ValueError(f"Height must be a positive number, got {height} instead.")
    
    # check if floor is on the XY plane, by subtracting the Z coordinate from point 0 to all points
    if not all(p.z == floor.points[0].z for p in floor.points):
        raise ValueError("The floor polygon must be on the XY plane, all points must have the same Z coordinate.")

    def to_wall(p1: Point, p2: Point, height: float) -> Polygon:
        return Polygon([
            p1,
            p2,
            Point(p2.x, p2.y, p2.z + height),
            Point(p1.x, p1.y, p1.z + height)
        ])
    
    walls = []
    for i in range(len(floor.points) - 1):
        walls.append(to_wall(floor.points[i], floor.points[i + 1], height))

    # close the last wall
    walls.append(to_wall(floor.points[-1], floor.points[0], height))
    return walls

class Points(object):
    def __init__(self, point_to_evaluate):
        self.point_to_evaluate = point_to_evaluate


def calc_windows_walls(facade_list: list[Polygon], 
                       wwr: float, 
                       potentially_intersecting_solids: list[OCCBrep],
                       ) -> tuple[list[Polygon], 
                                  list[Polygon], 
                                  list[Vector], 
                                  list[Vector], 
                                  list[Literal[0, 1]]]:
    """
    Classify each façade face as window or wall, generate any required geometry 
    (triangulated wall panels, punched windows), and return normals plus an intersection flag.

    :param facade_list: a list of vertical faces representing the facades of a building.
    :type facade_list: list[OCCface]
    :param wwr: window to wall ratio, ranges from 0 to 1.
    :type wwr: float
    :param potentially_intersecting_solids: 
        all buildings from the site that might intersect with the currently analysed building facade. 
        It could be an empty list, but if it's not, it will contain the building itself as well.
    :type potentially_intersecting_solids: list[OCCsolid]
    :raises ValueError: if wwr is not `float` or cannot be turned into `float`, raise ValueError.
    :return: windows on the facade surfaces.
    :rtype: list[OCCface]
    :return: opaque wall faces (triangulated where windows were created).
    :rtype: list[OCCface]
    :return: window surface normal vectors.
    :rtype: list[tuple[float, float, float]]
    :return: unit normals for every element in the previous *wall_list* 
    (duplicates exist because walls may be triangulated).
    :rtype: list[tuple[float, float, float]]
    :return: `1` if the original surface intersects with any other solid, or `0` otherwise.
    :rtype: list[Literal[0, 1]]
    """
    window_list: list[Polygon] = []
    wall_list: list[Polygon] = []
    normals_win: list[Vector] = []
    normals_wall: list[Vector] = []
    wall_intersects: list[Literal[0, 1]] = []
    for surface_facade in facade_list:
        # get coordinates of surface
        ref_pypt = surface_facade.centroid
        standard_normal = surface_facade.normal

        # evaluate if the surface intersects any other solid (important to erase non-active surfaces in the building
        # simulation model)
        data_point: Point = ref_pypt.translated(standard_normal.scaled(0.1))
        intersects = 0
        for solid in potentially_intersecting_solids:
            intersects += calc_intersection_face_solid(solid, data_point)
            if intersects > 0:
                break

        if intersects > 0:  # the face intersects so it is a partition wall, and no window is created
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
                window, hollowed_facades = create_windows(surface_facade, wwr)
                window_list.append(window)
                normals_win.append(standard_normal)
                # for walls
                wall_intersects.extend([intersects if intersects in (0, 1) else 0 for _ in range(len(hollowed_facades))])
                wall_list.extend(hollowed_facades)
                normals_wall.extend([standard_normal] * len(hollowed_facades))

            elif wwr == 1.0:
                window_list.append(surface_facade)
                normals_win.append(standard_normal)
            else:
                wall_list.append(surface_facade)
                normals_wall.append(standard_normal)
                wall_intersects.append(1 if intersects else 0)

    return window_list, wall_list, normals_win, normals_wall, wall_intersects


def calc_intersection_face_solid(potentially_intersecting_solid: OCCBrep, point: Point):
    with cea.utilities.devnull():
        # compas_occ did not implement point in solid check, so we use OCC directly
        state = BRepClass3d_SolidClassifier(
            potentially_intersecting_solid.occ_shape,
            gp_Pnt(point.x, point.y, point.z),
            1e-6,
        )
        point_in_solid = state.State() == TopAbs_IN
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

    def generate_tin(self, tolerance=1e-6) -> Mesh:
        """generates a 3D mesh from the elevation raster map.

        :param tolerance: The minimal surface area of each triangulated face. 
            Any faces smaller than the tolerance will be deleted. Defaults to `1e-6`.
        :type tolerance: float, optional
        :return: a list of OCCface triangles representing the 3D mesh of the terrain.
        :rtype: list[OCCface]
        """
        # Ignore no data values from raster
        y_index, x_index = np.nonzero(self.elevation_map != self.nodata)
        _x_coords = self.x_coords[x_index]
        _y_coords = self.y_coords[y_index]

        raster_points_list = [[float(x), float(y), float(z)] for x, y, z in zip(_x_coords, _y_coords, self.elevation_map[y_index, x_index])]
        decimals = int(round(-math.log10(tolerance)))
        tin_mesh = Mesh.from_points(raster_points_list)
        tin_mesh.weld(precision=decimals)  # Ensure the mesh is welded to remove duplicate vertices
        return tin_mesh


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


def tree_geometry_generator(tree_df: gpd.GeoDataFrame, terrain_raster: gdal.Dataset) -> list[list[Polygon]]:
    terrian_projection = terrain_raster.GetProjection()
    proj4_str = osr.SpatialReference(wkt=terrian_projection).ExportToProj4()
    tree_df = tree_df.to_crs(proj4_str)

    elevation_map = ElevationMap.read_raster(terrain_raster)

    from multiprocessing import cpu_count
    from multiprocessing.pool import Pool

    with Pool(cpu_count() - 1) as pool:
        surfaces = [
            [face.to_polygon() for face in solid.faces]
            for (solid, _) in pool.starmap(
                process_geometries,
                (
                    (geom, elevation_map, (0, 1), z)
                    for geom, z in zip(tree_df["geometry"], tree_df["height_tc"])
                ),
            )
        ]

    return surfaces


def geometry_main(config: cea.config.Configuration, 
                  zone_df: gpd.GeoDataFrame, 
                  surroundings_df: gpd.GeoDataFrame, 
                  trees_df: gpd.GeoDataFrame, 
                  terrain_raster: gdal.Dataset, 
                  architecture_wwr_df: pd.DataFrame, 
                  geometry_pickle_dir: str,
                  ) -> tuple[Mesh, 
                             list[str], 
                             list[str], 
                             list[list[Polygon]]]:
    """reads the input data of a scenario, generates and stores 3D data of each building, 
    and generate 3D geometry of the terrain.

    :param config: Configuration object with the settings (general and radiation)
    :type config: cea.config.Configuration
    :param zone_df: data and 2D geometry of all analyzed building in the site, typically read from `zone.shp`.
    :type zone_df: gpd.GeoDataFrame
    :param surroundings_df: data and 2D geometry of surrounding buildings.
    :type surroundings_df: gpd.GeoDataFrame
    :param trees_df: geometry and data of trees in the site (if any).
    :type trees_df: gpd.GeoDataFrame
    :param terrain_raster: the raw terrain grayscale graph containing elevation information.
    :type terrain_raster: gdal.Dataset
    :param architecture_wwr_df: detailed envelope information of each building.
    :type architecture_wwr_df: pd.DataFrame
    :param geometry_pickle_dir: directory where building 3D geometry data is stored.
    :type geometry_pickle_dir: str
    :return: a list of OCCface triangles representing the 3D mesh of the terrain.
    :rtype: list[OCCface]
    :return: names of analyzed buildings within the scenario.
    :rtype: list[str]
    :return: names of surrounding buildings within the scenario.
    :rtype: list[str]
    :return: list of tree geometries (if any)
    :rtype: list[list[OCCface]]
    """
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

    tree_surfaces: list[list[Polygon]] = []
    if len(trees_df.geometry) > 0:
        print("Creating tree surfaces")
        tree_surfaces = tree_geometry_generator(trees_df, terrain_raster)

    return terrain_tin, geometry_3D_zone, geometry_3D_surroundings, tree_surfaces


if __name__ == '__main__':
    import geopandas as gpd
    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    zone_path = locator.get_zone_geometry()
    surroundings_path = locator.get_surroundings_geometry()
    trees_path = locator.get_tree_geometry()
    zone_df = gpd.GeoDataFrame.from_file(zone_path)
    surroundings_df = gpd.GeoDataFrame.from_file(surroundings_path)

    if os.path.exists(trees_path):
        print(f"trees: {trees_path}")
        trees_df = gpd.GeoDataFrame.from_file(trees_path)
    else:
        print("trees: None")
        # Create empty area if it does not exist
        trees_df = gpd.GeoDataFrame(geometry=[], crs=zone_df.crs)

    geometry_staging_location = os.path.join(locator.get_solar_radiation_folder(), "radiance_geometry_pickle")

    print("Creating 3D geometry and surfaces")
    print(f"Saving geometry pickle files in: {geometry_staging_location}")
    # create geometrical faces of terrain and buildings
    terrain_raster = gdal.Open(locator.get_terrain())
    architecture_wwr_df = gpd.GeoDataFrame.from_file(locator.get_building_architecture()).set_index('name')

    # run routine City GML LOD 1
    time1 = time.time()
    (
        geometry_terrain,
        zone_building_names,
        surroundings_building_names,
        tree_surfaces,
    ) = geometry_main(
        config,
        zone_df,
        surroundings_df,
        trees_df,
        terrain_raster,
        architecture_wwr_df,
        geometry_staging_location,
    )

    # # to visualize the results
    # geometry_buildings = []
    # geometry_buildings_nonop = []
    # walls_intercept = [val for sublist in geometry_3D_zone for val, inter in
    #                    zip(sublist['walls'], sublist['intersect_walls']) if inter > 0]
    # windows = [val for sublist in geometry_3D_zone for val in sublist['windows']]
    # walls = [val for sublist in geometry_3D_zone for val in sublist['walls']]
    # roofs = [val for sublist in geometry_3D_zone for val in sublist['roofs']]
    # footprint = [val for sublist in geometry_3D_zone for val in sublist['footprint']]
    # walls_s = [val for sublist in geometry_3D_surroundings for val in sublist['walls']]
    # windows_s = [val for sublist in geometry_3D_surroundings for val in sublist['windows']]
    # roof_s = [val for sublist in geometry_3D_surroundings for val in sublist['roofs']]

    # geometry_buildings_nonop.extend(windows)
    # geometry_buildings_nonop.extend(windows_s)
    # geometry_buildings.extend(walls)
    # geometry_buildings.extend(roofs)
    # geometry_buildings.extend(footprint)
    # geometry_buildings.extend(walls_s)
    # geometry_buildings.extend(roof_s)
    # normals_terrain = calculate.face_normal_as_edges(geometry_terrain, 5)
    # utility.visualise([geometry_terrain, geometry_buildings, geometry_buildings_nonop, walls_intercept],
    #                   ["GREEN", "WHITE", "BLUE", "RED"])  # install Wxpython

    # utility.visualise([walls_intercept],
    #                   ["RED"])

    # utility.visualise([walls],
    #                   ["RED"])

    # utility.visualise([windows],
    #                   ["RED"])
