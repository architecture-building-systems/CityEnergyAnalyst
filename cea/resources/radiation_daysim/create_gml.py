import pyliburo.py3dmodel.construct as construct
import pyliburo.py3dmodel.fetch as fetch
import pyliburo.py3dmodel.calculate as calculate
import pyliburo.py3dmodel.modify as modify
import pyliburo.pycitygml as pycitygml
import pyliburo.gml3dmodel as gml3dmodel
import pyliburo.shp2citygml as shp2citygml

from OCC.IntCurvesFace import IntCurvesFace_ShapeIntersector
from OCC.gp import gp_Pnt, gp_Lin, gp_Ax1, gp_Dir
from geopandas import GeoDataFrame as gdf
import shapefile
import cea.globalvar
import cea.inputlocator
import numpy as np
import gdal
import time

__author__ = "Paul Neitzel, Kian Wee Chen"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Paul Neitzel", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

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

def building2d23d(citygml_writer, zone_shp_path, district_shp_path, tin_occface_list,
                  height_col, nfloor_col):
    """
    This script extrudes buildings from the shapefile and creates intermediate floors.

    :param citygml_writer: the cityGML object to which the buildings are gonna be created.
    :param district_shp_path: path to the shapefile to be extruded of the district
    :param tin_occface_list: the faces of the terrain, to be used to put the buildings on top.
    :param height_col:
    :param nfloor_col:
    :return:
    """
    # read district shapefile and names of buildings of the zone of analysis
    district_building_records = gdf.from_file(district_shp_path).set_index('Name')
    district_building_names = district_building_records.index.values
    zone_building_names = gdf.from_file(zone_shp_path)['Name'].values

    #make shell out of tin_occface_list and create OCC object
    terrain_shell = construct.make_shell_frm_faces(tin_occface_list)[0]
    terrain_intersection_curves = IntCurvesFace_ShapeIntersector()
    terrain_intersection_curves.Load(terrain_shell, 1e-6)
    bsolid_list = []

    #create the buildings in 3D
    for name in district_building_names:
        height = float(district_building_records.loc[name, height_col])
        nfloors = int(district_building_records.loc[name, nfloor_col])

        # Make floors only for the buildings of the zone of interest
        # for the rest just consider one high floor.
        # simplify geometry tol =1 for buildings of interest, tol = 5 for surroundings
        if name in zone_building_names:
            range_floors = range(nfloors+1)
            flr2flr_height = height / nfloors
            geometry = district_building_records.ix[name].geometry.simplify(1, preserve_topology=True)
        else:
            range_floors = [0,1]
            flr2flr_height = height
            geometry = district_building_records.ix[name].geometry.simplify(5, preserve_topology=True)


        point_list_2D = list(geometry.exterior.coords)
        point_list_3D = [(a,b,0) for (a,b) in point_list_2D] # add 0 elevation

        #creating floor surface in pythonocc
        face = construct.make_polygon(point_list_3D)
        #get the midpt of the face
        face_midpt = calculate.face_midpt(face)

        #project the face_midpt to the terrain and get the elevation
        inter_pt, inter_face = calc_intersection(terrain_intersection_curves, face_midpt, (0, 0, 1))

        loc_pt = fetch.occpt2pypt(inter_pt)
        #reconstruct the footprint with the elevation
        face = fetch.shape2shapetype(modify.move(face_midpt, loc_pt, face))

        moved_face_list = []
        for floor_counter in range_floors:
            dist2mve = floor_counter*flr2flr_height
            #get midpt of face
            orig_pt = calculate.face_midpt(face)
            #move the pt 1 level up
            dest_pt = modify.move_pt(orig_pt, (0,0,1), dist2mve)
            moved_face = modify.move(orig_pt, dest_pt, face)
            moved_face_list.append(moved_face)

        #loft all the faces and form a solid
        vertical_shell = construct.make_loft(moved_face_list)
        vertical_face_list = fetch.geom_explorer(vertical_shell, "face")
        roof = moved_face_list[-1]
        footprint = moved_face_list[0]
        all_faces = []
        all_faces.append(footprint)
        all_faces.extend(vertical_face_list)
        all_faces.append(roof)
        bldg_shell_list = construct.make_shell_frm_faces(all_faces)

        # make sure all the normals are correct (they are pointing out)
        if bldg_shell_list:
            bldg_solid = construct.make_solid(bldg_shell_list[0])
            bldg_solid = modify.fix_close_solid(bldg_solid)
            bsolid_list.append(bldg_solid)
            occface_list = fetch.geom_explorer(bldg_solid, "face")
            geometry_list = gml3dmodel.write_gml_srf_member(occface_list)
            citygml_writer.add_building("lod1", name,geometry_list)

    return bsolid_list

def terrain2d23d(citygml_writer, input_terrain_raster):

    # read x, y, z coordinates of raster
    raster_points = raster_reader(input_terrain_raster)

    #create tin and triangulate
    tin_occface_list = construct.delaunay3d(raster_points)

    geometry_list = gml3dmodel.write_gml_triangle(tin_occface_list)
    citygml_writer.add_tin_relief("lod1", "terrain1", geometry_list)
    return tin_occface_list

def raster_reader(input_terrain_raster):

    # read raster records
    raster_dataset = gdal.Open(input_terrain_raster)
    band = raster_dataset.GetRasterBand(1)
    a = band.ReadAsArray(0, 0, raster_dataset.RasterXSize, raster_dataset.RasterYSize)
    (y_index, x_index) = np.nonzero(a >= 0)
    (upper_left_x, x_size, x_rotation, upper_left_y, y_rotation, y_size) = raster_dataset.GetGeoTransform()
    x_coords = x_index * x_size + upper_left_x + (x_size / 2)  # add half the cell size
    y_coords = y_index * y_size + upper_left_y + (y_size / 2)  # to centre the point

    return [(x, y, z) for x, y, z in zip(x_coords, y_coords, a[y_index, x_index])]

def create_citygml(zone_shp_path, district_shp_path, input_terrain, output_folder):

    # local variables
    citygml_writer = pycitygml.Writer()

    # transform terrain to CityGML
    terrain_face_list = terrain2d23d(citygml_writer, input_terrain)
    
    # transform buildings to
    bsolid_list = building2d23d(citygml_writer, zone_shp_path, district_shp_path, terrain_face_list,
                                height_col='height_ag', nfloor_col="floors_ag")

    #construct.visualise([terrain_face_list,bsolid_list], ["GREEN","WHITE"], backend = "wx") #install Wxpython

    # write to citygml
    citygml_writer.write(output_folder)

if __name__ == '__main__':

    # import modules
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario=scenario_path)

    # local variables
    output_folder = locator.get_building_geometry_citygml()
    district_shp = locator.get_district()
    zone_shp = locator.get_zone_geometry()
    input_terrain_raster = locator.get_terrain()

    # run routine City GML LOD 1
    time1 = time.time()
    create_citygml(zone_shp, district_shp, input_terrain_raster, output_folder)
    print "CityGml creation finished in ", (time.time() - time1) / 60.0, " mins"





