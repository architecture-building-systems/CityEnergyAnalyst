# ==================================================================================================
#
#    Copyright (c) 2016, Chen Kian Wee (chenkianwee@gmail.com)
#
#    This file is part of pyliburo
#
#    pyliburo is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    pyliburo is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Dexen.  If not, see <http://www.gnu.org/licenses/>.
#
# ==================================================================================================
import py3dmodel
import threedmodel

#==============================================================================================================================
#shp2citygml functions
#==============================================================================================================================
def make_transit_stop_box(length, width, height):
    box = py3dmodel.construct.make_box(length, width, height)
    return box
    
def create_transit_stop_geometry(occ_transit_box_shape, location_pt):
    trsf_shp = py3dmodel.modify.move((0,0,0), location_pt, occ_transit_box_shape)
    return trsf_shp

def extrude_building(building_footprint, height):
    face_list = []
    #polygons from shpfiles are always clockwise
    #holes are always counter-clockwise
    extrude = py3dmodel.construct.extrude(building_footprint,(0,0,1), height )
    extrude = py3dmodel.fetch.shape2shapetype(extrude)
    face_list = py3dmodel.fetch.faces_frm_solid(extrude)
    return face_list
    
def landuse_surface_cclockwise(pypt_list):
    luse_f = py3dmodel.construct.make_polygon(pypt_list)
    n = py3dmodel.calculate.face_normal(luse_f)
    if not py3dmodel.calculate.is_anticlockwise(pypt_list, n):
        luse_f.Reverse()
        
    luse_pts = py3dmodel.fetch.pyptlist_frm_occface(luse_f)
    return luse_pts
    
#==============================================================================================================================
#citygml2eval functions
#==============================================================================================================================
def generate_sensor_surfaces(occ_face, xdim, ydim):
    normal = py3dmodel.calculate.face_normal(occ_face)
    mid_pt = py3dmodel.calculate.face_midpt(occ_face)
    location_pt = py3dmodel.modify.move_pt(mid_pt, normal, 0.01)
    moved_oface = py3dmodel.fetch.shape2shapetype(py3dmodel.modify.move(mid_pt, location_pt, occ_face))
    #put it into occ and subdivide surfaces 
    sensor_surfaces = py3dmodel.construct.grid_face(moved_oface, xdim, ydim)
    sensor_pts = []
    sensor_dirs = []
    for sface in sensor_surfaces:
        smidpt = py3dmodel.calculate.face_midpt(sface)
        sensor_pts.append(smidpt)
        sensor_dirs.append(normal)
    
    return sensor_surfaces, sensor_pts, sensor_dirs
        
def identify_srfs_according_2_angle(occfacelist):
    roof_list = []
    facade_list = []
    footprint_list = []
    vec1 = (0,0,1)
    for f in occfacelist:
        #get the normal of each face
        n = py3dmodel.calculate.face_normal(f)
        angle = py3dmodel.calculate.angle_bw_2_vecs(vec1, n)
        #means its a facade
        if angle>45 and angle<135:
            facade_list.append(f)
        elif angle<=45:
            
            roof_list.append(f)
        elif angle>=135:
            footprint_list.append(f)
    return facade_list, roof_list, footprint_list
            
def identify_building_surfaces(bsolid):
    face_list = py3dmodel.fetch.faces_frm_solid(bsolid)
    facade_list, roof_list, footprint_list = identify_srfs_according_2_angle(face_list)     
    return facade_list, roof_list, footprint_list
    
def faces_surface_area(occ_facelist):
    total_sa = 0
    for occface in occ_facelist:
        sa = py3dmodel.calculate.face_area(occface)
        total_sa = total_sa + sa
    return total_sa
    
#==============================================================================================================================
#gmlparameterise functions
#==============================================================================================================================
def get_building_footprint(building_solid):
    face_list = py3dmodel.fetch.faces_frm_solid(building_solid)
    
    for face in face_list:
        normal = py3dmodel.calculate.face_normal(face)
        if normal == (0,0,-1):
            fpt_list = face
            return fpt_list
            
def get_building_solid(building, citygml_reader):
    pypolygon_list = citygml_reader.get_pypolygon_list(building)
    solid = threedmodel.pypolygons2occsolid(pypolygon_list)
    return solid
    
def get_building_height_storey(building, citygml_reader):
    height = citygml_reader.get_building_height(building)
    storey = citygml_reader.get_building_storey(building)
    storey_height = height/storey
    return height, storey, storey_height
    
def get_building_bounding_footprint(building_solid):
    xmin, ymin, zmin, xmax, ymax, zmax = py3dmodel.calculate.get_bounding_box(building_solid)
    bounding_footprint = py3dmodel.construct.make_polygon([(xmin,ymin,zmin),(xmin,ymax,zmin),(xmax, ymax, zmin),(xmax, ymin, zmin)])
    return bounding_footprint
    
def get_building_location_pt(building_solid):
    bounding_footprint = get_building_bounding_footprint(building_solid)
    loc_pt = py3dmodel.calculate.face_midpt(bounding_footprint)
    return loc_pt, bounding_footprint
    
    
def construct_building_through_floorplates(building_solid, build_area, storey_height, citygml_reader):
    intersection_list = []
    bounding_list = []
    loc_pt, bounding_footprint = get_building_location_pt(building_solid)
    
    scnt = 0
    while build_area > 0:
        if scnt == 0:
            #get the building footprint 
            building_footprint_face = get_building_footprint(building_solid)
            flr_area = py3dmodel.calculate.face_area(building_footprint_face)
            build_area = build_area - flr_area
            intersection_list.append(building_footprint_face)
            
        else:
            z = loc_pt[2]+((scnt)*storey_height)
            moved_pt = (loc_pt[0], loc_pt[1], z)
            moved_f = py3dmodel.modify.move(loc_pt, moved_pt, bounding_footprint)
            bounding_list.append(py3dmodel.fetch.shape2shapetype(moved_f))
            floors = py3dmodel.construct.boolean_common(building_solid, moved_f)
                
            compound = py3dmodel.fetch.shape2shapetype(floors)
            inter_face_list = py3dmodel.fetch.topos_frm_compound(compound)["face"]
            if inter_face_list:
                for inter_face in inter_face_list:
                    flr_area = py3dmodel.calculate.face_area(inter_face)
                    build_area = build_area - flr_area
                    intersection_list.append(inter_face)
            else:
                #it means the original solid is not so tall
                #need to move a storey up 
                loc_pt2 = (moved_pt[0], moved_pt[1], (moved_pt[2]-storey_height))
                previous_flr = intersection_list[-1]
                moved_f2 = py3dmodel.fetch.shape2shapetype(py3dmodel.modify.move(loc_pt2, moved_pt, previous_flr))
                flr_area = py3dmodel.calculate.face_area(moved_f2)
                build_area = build_area - flr_area
                intersection_list.append(moved_f2)

        scnt += 1
            
    last_flr = intersection_list[-1]
    rs_midpt = py3dmodel.calculate.face_midpt(last_flr)
    moved_pt = (rs_midpt[0], rs_midpt[1], (rs_midpt[2]+storey_height))
    roof_srf = py3dmodel.fetch.shape2shapetype(py3dmodel.modify.move(rs_midpt, moved_pt, last_flr))

    intersection_list.append(roof_srf)
    flr_srf = intersection_list[0]
    
    new_building_shell = py3dmodel.construct.make_loft(intersection_list, rule_face = False)
    
    face_list = py3dmodel.fetch.faces_frm_shell(new_building_shell) 
    face_list.append(roof_srf)
    face_list.append(flr_srf)
    closed_shell = py3dmodel.construct.make_shell_frm_faces(face_list)
    shell_list = py3dmodel.fetch.topos_frm_compound(closed_shell)["shell"]
    new_building_solid = py3dmodel.construct.make_solid(shell_list[0])
    
    return new_building_solid, intersection_list, bounding_list
    
def get_bulding_flrplates(building_solid, loc_pt, bounding_footprint, nstorey, storey_height, building_footprint):
    intersection_list = []
    bounding_list = []
    for scnt in range(nstorey):
        if scnt == 0:
            intersection_list.append(building_footprint)
        else:
            z = loc_pt[2]+(scnt*storey_height)
            moved_pt = (loc_pt[0], loc_pt[1], z)
            moved_f = py3dmodel.modify.move(loc_pt, moved_pt, bounding_footprint)
            bounding_list.append(moved_f)
            floors = py3dmodel.construct.boolean_common(building_solid, moved_f)
            compound = py3dmodel.fetch.shape2shapetype(floors)
            inter_face_list = py3dmodel.fetch.topos_frm_compound(compound)["face"]
            if inter_face_list:
                for inter_face in inter_face_list:
                    intersection_list.append(inter_face)
                    
    return intersection_list#, bounding_list
    
def get_building_combined_footprint(building_solid, loc_pt, bounding_footprint, nstorey, storey_height, building_footprint):
    flrplates = get_bulding_flrplates(building_solid, loc_pt, bounding_footprint, nstorey, storey_height, building_footprint)
    building_footprint_pts = py3dmodel.pyptlist_frm_occface(building_footprint)
    elev_ftprint = building_footprint_pts[0][2] #assuming the footprint is flat 
    #project each footprint onto the footprint
    new_flrs = []
    for flr in flrplates:
        flrpts = py3dmodel.pyptlist_frm_occface(flr)
        projected_flrpts = []
        for fp in flrpts:
            new_fp = [fp[0],fp[1],elev_ftprint]
            projected_flrpts.append(new_fp)
            
        new_flr = py3dmodel.construct.make_polygon(projected_flrpts)
        new_flrs.append(new_flr)
        
    fcnt = 0
    for nf in new_flrs:
        if fcnt == 0:
            fused = py3dmodel.construct.boolean_fuse(nf, new_flrs[fcnt+1])
        elif fcnt < len(new_flrs)-1 and fcnt > 0:
            fused = py3dmodel.construct.boolean_fuse(fused, new_flrs[fcnt+1])
        fcnt +=1
        
    return py3dmodel.fetch.shape2shapetype(fused)
            
def get_bulding_floor_area(building_solid, loc_pt, bounding_footprint, nstorey, storey_height, building_footprint):
    flr_plates = get_bulding_flrplates(building_solid, loc_pt, bounding_footprint, nstorey, storey_height, building_footprint)
    flr_area = 0
    for flr in flr_plates:
        flr_area = flr_area + py3dmodel.calculate.face_area(flr)
        
    return flr_area #, intersection_list
    
def buildings_on_landuse(landuse_occpolygon, buildings_footprints_dict_list):
    buildings_on_plot_list = []
    
    for building in buildings_footprints_dict_list:
        fp = building["footprint"]
        if py3dmodel.calculate.face_is_inside(fp, landuse_occpolygon):
            buildings_on_plot_list.append(building)
    
    return buildings_on_plot_list
    
def surface_area(surface_pts):
    face = py3dmodel.construct.make_polygon(surface_pts)
    area = py3dmodel.calculate.face_area(face)
    return area
    
def landuse_2_grid(landuse_face, xdim, ydim):
    pt_list = []
    grid_faces = py3dmodel.construct.grid_face(landuse_face, xdim, ydim)
    for f in grid_faces:
        pt = py3dmodel.calculate.face_midpt(f)
        pt_list.append(pt)
        
    return pt_list, grid_faces
    
def b_attrib_list2_unmoved(b_attribs_list):
    for b in b_attribs_list:
        b["location_status"] = "unmoved"
    return b_attribs_list
    
def is_solid_common(solid1, solid2):
    is_solid_common = False
    intersection = py3dmodel.construct.boolean_common(solid1, solid2)
    compound = py3dmodel.fetch.shape2shapetype(intersection)
    iscompundnull = py3dmodel.fetch.is_compound_null(compound)
    if not iscompundnull:
        is_solid_common = True
    return is_solid_common

def rearrange_building_location(b_attribs_list, landuse_pts, parameters, xdim, ydim):
    luse_face = py3dmodel.construct.make_polygon(landuse_pts)
    grid_luse, grid_faces = landuse_2_grid(luse_face, xdim, ydim)
    npts = len(grid_luse)
    moved_buildings_attribs_list = []
    moved_buildings = []
    
    bcnt = 0
    for building in b_attribs_list:
        loc_pt = building["loc_pt"]
        
        #rotate the building solid 
        rot_cnt = building["gcnt"][0]
        n_rotate_parameter = parameters[rot_cnt]
        rotate_parameter = n_rotate_parameter*360
        solid = building["solid"]
        rot_solid = py3dmodel.modify.rotate(solid, loc_pt, (0,0,1), rotate_parameter)
        
        #map the location point to the grid points
        loc_cnt = building["gcnt"][1]
        n_loc_parameter = parameters[loc_cnt]
        loc_parameter = int(n_loc_parameter*(npts-1))
        
        isclash = True
        for clash_cnt in range(npts):
            #print "clash_cnt", clash_cnt
            mpt_index = loc_parameter+clash_cnt
            if mpt_index >= npts:
                mpt_index = mpt_index-(npts-1) 
                
            moved_pt = grid_luse[mpt_index]
            moved_solid = py3dmodel.fetch.shape2shapetype(py3dmodel.modify.move(loc_pt, moved_pt, rot_solid))
            
            #need to check if the moved building is within the boundaries of the landuse 
            bounding_footprint = get_building_bounding_footprint(moved_solid)
            
            if py3dmodel.calculate.face_is_inside(bounding_footprint, luse_face):
                #test if it clashes with the other buildings 
                if moved_buildings:
                    for mv_b in moved_buildings:
                        IsCommon = is_solid_common(moved_solid, mv_b)
                        if IsCommon:
                            isclash = True
                            break
                        elif not IsCommon:
                            #print "I am not clashing onto anyone!!!"
                            isclash = False
                            
                    #since there is no clash there is no need for a next round
                    if isclash == False:
                        break
                
                else:
                    isclash = False
                    break
                            
        if isclash == True:
            print "it is not feasible with these parameters to create a design variant"
            #just append the original arrangements into the list
            return b_attrib_list2_unmoved(b_attribs_list), grid_faces
        
        if isclash == False:
            #print "successfully positioned the building"
            moved_buildings.append(py3dmodel.fetch.shape2shapetype(moved_solid))
            moved_buildings_attrib = {}
            moved_buildings_attrib["solid"] = py3dmodel.fetch.shape2shapetype(moved_solid)
            moved_buildings_attrib["bounding_footprint"] = bounding_footprint
            moved_buildings_attrib["loc_pt"] = moved_pt
            moved_buildings_attrib["gcnt"] = building["gcnt"]
            moved_buildings_attrib["location_status"] = "moved"
            moved_buildings_attribs_list.append(moved_buildings_attrib)
            
        bcnt +=1
        
    print "successfully positioned the buildings"
    return moved_buildings_attribs_list, grid_faces