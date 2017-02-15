import os
import pyliburo.py3dmodel.construct as construct
import pyliburo.py3dmodel.fetch as fetch
import pyliburo.py3dmodel.calculate as calculate
import pyliburo.py3dmodel.modify as modify
import pyliburo.pycitygml as pycitygml
import pyliburo.gml3dmodel as gml3dmodel
import pyliburo.shp2citygml as shp2citygml
import shapefile
import cea.globalvar
import cea.inputlocator
from OCC.StlAPI import StlAPI_Writer
import pandas as pd

__author__ = "Paul Neitzel"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Paul Neitzel", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def building2d23d(shapefilepath, out_path, height_col, elev_col, name_col,nfloor_col):
    citygml_writer = pycitygml.Writer()
    sf = shapefile.Reader(shapefilepath)
    shapeRecs = sf.shapeRecords()
    field_name_list = shp2citygml.get_field_name_list(sf)
    height_index = field_name_list.index(height_col) - 1
    name_index = field_name_list.index(name_col) - 1
    elev_index = field_name_list.index(elev_col) - 1
    floor_index = field_name_list.index(nfloor_col) - 1
    rcnt = 0
    for rec in shapeRecs:
        poly_attribs = rec.record
        height = float(poly_attribs[height_index])
        elev = float(poly_attribs[elev_index])
        name = str(poly_attribs[name_index])
        nfloors = int(poly_attribs[floor_index])
        part_list = shp2citygml.get_geometry(rec)
        for part in part_list:
            point_list = shp2citygml.pypt_list2d_2_3d(part, elev)
            face = construct.make_polygon(point_list)
            flr2flr_height = height/nfloors
            moved_face_list = []
            for flrcnt in range(nfloors+1):
                dist2mve = flrcnt*flr2flr_height
                #get midpt of face
                orig_pt = calculate.face_midpt(face)
                #move the pt 1 level up 
                dest_pt = modify.move_pt(orig_pt, (0,0,1), dist2mve)
                moved_face = modify.move(orig_pt, dest_pt, face)
                moved_face_list.append(moved_face)
            
            #loft all the face to form a solid
            vertical_shell = construct.make_loft(moved_face_list)
            vertical_face_list = fetch.geom_explorer(vertical_shell, "face")
            roof = moved_face_list[-1]
            footprint = moved_face_list[0]
            all_faces = []
            all_faces.append(footprint)
            all_faces.extend(vertical_face_list)
            all_faces.append(roof)
            bldg_shell_list = construct.make_shell_frm_faces(all_faces)
            if bldg_shell_list:
                bldg_solid = construct.make_solid(bldg_shell_list[0])
                bldg_solid = modify.fix_close_solid(bldg_solid)
                occface_list = fetch.geom_explorer(bldg_solid, "face")
                geometry_list = gml3dmodel.write_gml_srf_member(occface_list)
                citygml_writer.add_building("lod1", name,geometry_list)
        rcnt+=1
        
    citygml_writer.write(os.path.join(out_path,'new.gml'))
    
if __name__ == '__main__':
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    output_folder = locator.get_3D_geometry_folder()
    input_shapefile= locator.get_building_geometry_with_elevation()
    building_solids = building2d23d(input_shapefile, output_folder, height_col='height_ag', name_col='Name', elev_col='DN', nfloor_col = "floors_ag")







