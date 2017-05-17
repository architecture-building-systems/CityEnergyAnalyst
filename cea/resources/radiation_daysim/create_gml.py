import pyliburo.py3dmodel.construct as construct
import pyliburo.py3dmodel.fetch as fetch
import pyliburo.py3dmodel.calculate as calculate
import pyliburo.py3dmodel.modify as modify
import pyliburo.pycitygml as pycitygml
import pyliburo.gml3dmodel as gml3dmodel
import pyliburo.shp2citygml as shp2citygml
from geopandas import GeoDataFrame as gdf
import shapefile
import cea.globalvar
import cea.inputlocator
import numpy as np
import gdal

__author__ = "Paul Neitzel, Kian Wee Chen"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Paul Neitzel", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


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

    #make shell out of tin_occface_list
    terrain_shell = construct.make_shell_frm_faces(tin_occface_list)[0]
    bsolid_list = []
    #create the buildings in 3D
    for name in district_building_names:
        height = float(district_building_records.loc[name, height_col])
        nfloors = int(district_building_records.loc[name, nfloor_col])
        point_list_2D = list(district_building_records.ix[name].geometry.exterior.coords)
        point_list_3D = [(a,b,0) for (a,b) in point_list_2D] # add 0 elevation

        #creating floor surface in pythonocc
        face = construct.make_polygon(point_list_3D)
        #get the midpt of the face
        face_midpt = calculate.face_midpt(face)
        #project the face_midpt to the terrain and get the elevation
        inter_pt, inter_face = calculate.intersect_shape_with_ptdir(terrain_shell,face_midpt, (0,0,1))
        loc_pt = fetch.occpt2pypt(inter_pt)
        #reconstruct the footprint with the elevation
        face = fetch.shape2shapetype(modify.move(face_midpt, loc_pt, face))

        # Make floors only for the buildings of the zone of interest
        if name in zone_building_names:
            range_floors = range(nfloors+1)
            flr2flr_height = height / nfloors
        # for the rest just consider one high floor.
        else:
            range_floors = [0,1]
            flr2flr_height = height

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

    construct.visualise([terrain_face_list,bsolid_list], ["GREEN","WHITE"], backend = "wx") #install Wxpython

    # write to citygml
    citygml_writer.write(output_folder)

if __name__ == '__main__':

    # import modules
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)

    # local variables
    output_folder = locator.get_building_geometry_citygml()
    district_shp = locator.get_district()
    zone_shp = locator.get_building_geometry()
    input_terrain_raster = locator.get_terrain()

    # run routine City GML LOD 1
    create_citygml(zone_shp, district_shp, input_terrain_raster, output_folder)






