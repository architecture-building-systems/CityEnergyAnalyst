import os
import pyliburo.py3dmodel.construct as construct
import pyliburo.py3dmodel.fetch as fetch
import pyliburo.shp2citygml
import shapefile
import pyliburo.shp2citygml as one
import cea.globalvar
import cea.inputlocator
from OCC.StlAPI import StlAPI_Writer

__author__ = "Paul Neitzel"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Paul Neitzel", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def building2d23d(shapefilepath, out_path, height_col, elev_col, name_col,nfloor_col):
    sf = shapefile.Reader(shapefilepath)

    shapeRecs = sf.shapeRecords()
    field_name_list = one.get_field_name_list(sf)
    height_index = field_name_list.index(height_col) - 1
    name_index = field_name_list.index(name_col) - 1
    elev_index = field_name_list.index(elev_col) - 1
    floor_index = field_name_list.index(nfloor_col) - 1

    solid_list = []

    for rec in shapeRecs:
        poly_attribs = rec.record
        height = float(poly_attribs[height_index])
        elev = float(poly_attribs[elev_index])
        name = str(poly_attribs[name_index])
        nfloors = int(poly_attribs[floor_index])
        print name, height, elev,nfloors

        part_list = one.get_geometry(rec)
        # if it is a close the first and the last vertex is the same
        for part in part_list:
            # create a bounding box to boolean the terrain
            point_list = one.point_list2d_2_3d(part, elev)
            face = pyliburo.py3dmodel.construct.make_polygon(point_list)
            flr2flr_height = height/nfloors
            for flrcnt in range(nfloors):
                bbox = construct.extrude(face, (0, 0, 1), flr2flr_height)
                building_extrude_solid = pyliburo.py3dmodel.fetch.shape2shapetype(bbox)
                construct.

            solid_list.append(building_extrude_solid)

            StlAPI_Writer().Write(building_extrude_solid, os.path.join(out_path, name+'new.stl'), False)


if __name__ == '__main__':
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    output_folder = locator.get_3D_geometry_folder()
    input_shapefile= locator.get_building_geometry_with_elevation()
    building_solids = building2d23d(input_shapefile, output_folder, height_col='height_ag', name_col='Name', elev_col='DN', nfloor_col = "floors_ag")







