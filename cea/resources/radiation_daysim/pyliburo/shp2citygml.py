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
import re
import uuid
import shapefile

import pycitygml
import py3dmodel
import gml3dmodel

#=========================================================================================================================================
#map osm to citygml functions
#=========================================================================================================================================
def map_osm2citygml_landuse_function(landuse):
    if landuse == "residential":
        #residential
        function = "1010"
    if landuse == "transport":
        #special function area
        function = "1040"
    if landuse == "recreation_ground":
        #Sports, leisure and recreation
        function = "1130"
    if landuse == "education":
        #special function area
        function = "1040"
    if landuse == "commercial":
        #Industry and Business
        function = "1020"
    if landuse == "civic":
        #special function area
        function = "1040"
    if landuse == "mixed":
        #MIxed use
        function = "1030"
    if landuse == "place_of_worship":
        #special function area
        function = "1040"
    if landuse == "reserve":
        #special function area
        function = "1040"
    if landuse == "utility":
        #special function area
        function = "1040"
    if landuse == "health":
        #special function area
        function = "1040"
    else:
        #special function area
        function = "1040"
    return function

def map_osm2citygml_building_class(landuse):
    if landuse == "residential":
        #habitation
        bclass = "1000"
    if landuse == "transport":
        #traffic area
        bclass = "1170"
    if landuse == "recreation_ground":
        #recreation
        bclass = "1050"
    if landuse == "education":
        #schools education research 
        bclass = "1100"
    if landuse == "commercial":
        #business trade
        bclass = "1030"
    if landuse == "civic":
        #administration
        bclass = "1020"
    if landuse == "mixed":
        #habitation
        bclass = "1000"
    if landuse == "place_of_worship":
        #church instituition
        bclass = "1080"
    if landuse == "reserve":
        #function
        bclass = "1180"
    if landuse == "utility":
        #function
        bclass = "1180"
    if landuse == "health":
        #healthcare
        bclass = "1120"
    return bclass

def map_osm2citygml_building_function(landuse):
    if landuse == "residential":
        #residential building
        function = "1000"
    if landuse == "transport":
        #others
        function = "2700"
    if landuse == "recreation_ground":
        #others
        function = "2700"
    if landuse == "education":
        #building for education and research
        function = "2070"
    if landuse == "commercial":
        #business building
        function = "1150"
    if landuse == "civic":
        #public building
        function = "1960"
    if landuse == "mixed":
        #residential and commercial building
        function = "1080"
    if landuse == "place_of_worship":
        #place of worship
        function = "2260"
    if landuse == "reserve":
        #others
        function = "2700"
    if landuse == "utility":
        #others
        function = "2700"
    if landuse == "health":
        #building for health care
        function = "2300"
    return function

def map_osm2citygml_building_amenity_function(amenity):
    if amenity == "parking":
        #multi storey car park
        function = "1610"
    else:
        #others
        function = "2700"
    return function

def map_osm2citygml_trpst_complex_class(trpst):
    if trpst == "subway":
        #subway
        tclass = "1080"
        
    if trpst == "light_rail":
        #rail_traffic
        tclass = "1060"
        
    if trpst == "unclassified" or trpst == "tertiary" or\
    trpst == "service" or trpst == "secondary_link" or trpst == "secondary" or\
    trpst == "residential" or trpst == "primary" or trpst == "motoway_link" or trpst == "motorway" or trpst == "construction" :
        #road_traffic
        tclass = "1040"
    else:
        #others
        tclass = "1090"
        
    return tclass

def map_osm2citygml_trpst_complex_function(trpst):
    if trpst == "subway":
        #subway
        function = "1825"
    if trpst == "light_rail":
        #rail transport
        function = "1800"
    if trpst == "unclassified" or trpst == "tertiary" or\
    trpst == "service" or trpst == "secondary_link" or trpst == "secondary" or\
    trpst == "residential" or trpst == "primary" or trpst == "motoway_link" or trpst == "motorway" or trpst == "construction" :
        #road
        function = "1000"
    if trpst == "track":
        #hiking trail
        function = "1230"
    if trpst == "steps" or trpst == "path" or trpst == "footway":
        #footpath/footway
        function = "1220"
    if trpst == "cycleway":
        #bikeway/cyclepath
        function = "1240"
    else:
        #others
        function = "2700"
    return function

#=========================================================================================================================================
#get shapefile functions
#=========================================================================================================================================
def get_field_name_list(sf):
    fields = sf.fields
    field_name_list = []
    for field in fields:
        field_name_list.append(field[0])
    return field_name_list
            
def get_geometry(shape_record):
    #takes in a single shape record and extract the parts and point of a shape file
    part_list = []
    shape = shape_record.shape
    shapetype = shape.shapeType
    if shapetype == 5 or shapetype == 3:
        #A ring is a connected sequence of four or more
        #points that form a closed, non-self-intersecting loop
        #The rings of a polygon are referred to as its parts
        parts=shape.parts
        
        num_parts=len(parts)
        points=shape.points
        count_parts=0
        for part in parts:
            part_s = parts[count_parts]
            if count_parts==num_parts-1:
                part_e=len(points)
            else:
                part_e=parts[count_parts+1]
            part_points=points[part_s:part_e]
            part_list.append(part_points)
            count_parts+=1
        return part_list
         
def get_shpfile_epsg(shpfile):
    #read the qpj file and find out wat epsg is the file base on 
    qpj_filepath = shpfile.replace(".shp", ".qpj")
    qpj = open(qpj_filepath, "r")
    epsg_num = qpj.read().split(",")[-1]
    m = re.search('"(.+?)"', epsg_num)
    if m:
        epsg = m.group(1)
    else:
        epsg = ""
    return epsg

#=========================================================================================================================================
#calculate functions
#=========================================================================================================================================
def calc_residential_parking_area(total_build_up):
    #TODO: verify the carpark calculation
    #base on the building footprint estimate how high the multistorey carpark should be
    hsehold_size = 3.43 #based on census data
    avg_hse_size = 87.4 #based on census data
    num_of_hse = total_build_up/avg_hse_size
    plot_pop_size = num_of_hse * hsehold_size
    car_ownership = 9.4 #cars/100persons
    plot_car_pop = car_ownership*(plot_pop_size/100)
    motorbike_ownership = 2.6 #motobikes/100persons
    plot_bike_pop = motorbike_ownership*(plot_pop_size/100)
    parking_lot_size = 2.4*4.8 #m2
    motorbike_lot_size = 1*2.5 #m2
    total_carlot_size = num_of_hse*parking_lot_size #m2 minimum provision is one car for a house
    total_bikelot_size = plot_bike_pop*motorbike_lot_size #m2
    total_parklot_size = total_carlot_size + total_bikelot_size + (total_carlot_size*1) #(factoring in the aisle and ramps is in ratio 1:2 of the parking lot) #m2
    return total_parklot_size

#=========================================================================================================================================
#geometry related functions
#=========================================================================================================================================
def point2d_2_3d(point2d, z):
    point3d = (point2d[0],point2d[1],z)
    return point3d

def point_list2d_2_3d(point_list2d, z):
    pt_list3d = []
    for pt in point_list2d:
        pt3d = point2d_2_3d(pt, z)
        pt_list3d.append(pt3d)
        
    return pt_list3d

def get_buildings(shpfile):
    building_list = []
    sf = shapefile.Reader(shpfile)
    shapeRecs=sf.shapeRecords()
    shapetype = shapeRecs[0].shape.shapeType
    
    #shapetype 1 is point, 3 is polyline, shapetype 5 is polygon
    if shapetype ==5:
        field_name_list = get_field_name_list(sf)
        
        #the attributes are mainly base on the attributes from osm 
        building_index = field_name_list.index("building")-1
        amenity_index = field_name_list.index("amenity")-1
        parking_index = field_name_list.index("parking")-1
        name_index = field_name_list.index("name")-1
        building_l_index = field_name_list.index("building_l")-1
        id_index = field_name_list.index("id")-1
        
        for rec in shapeRecs:
            poly_attribs=rec.record
            building = poly_attribs[building_index]
            building.strip()
            
            #if the polygon has a building attribute it is a building footprint
            if not building.isspace():
                building_dict = {}
                #get the geometry of the building footprint
                geom = get_geometry(rec)
                #only create a building if the records have geometry information
                if geom:
                    building_dict["building"] = building
                    face_list = []
                    for pt_list2d in geom:
                        pt_list3d = point_list2d_2_3d(pt_list2d, 0.0)
                        face = py3dmodel.construct.make_polygon(pt_list3d)
                        face_list.append(face)
                    building_dict["geometry"] = face_list
                    
                    amenity = poly_attribs[amenity_index]
                    amenity.strip()
                    if not amenity.isspace():
                        building_dict["amenity"] = amenity
                        
                    parking = poly_attribs[parking_index]
                    parking.strip()
                    if not parking.isspace():
                        building_dict["parking"] = parking
                        
                    name = poly_attribs[name_index]
                    name.strip()
                    if not name.isspace():
                        building_dict["name"] = name
                        
                    building_l = poly_attribs[building_l_index]
                    building_l.strip()
                    if not building_l.isspace():
                        building_dict["building_l"] = int(building_l)
                    building_list.append(building_dict)
                    
                    id_ = poly_attribs[id_index]
                    if id_:
                        building_dict["id"] = id_
                
    return building_list
    
def face_almost_inside(occ_face, occ_boundary_face):
    '''
    this functions measures if occ_face is almost inside the boundary face. 
    Almost inside is define as 50% of the occ face is inside the boundary face
    '''
    #measure the srf area of the occ face
    occ_face_area = py3dmodel.calculate.face_area(occ_face)
    common = py3dmodel.construct.boolean_common(occ_face, occ_boundary_face)
    shapetype = py3dmodel.fetch.shape2shapetype(common)
    face_list = py3dmodel.fetch.geom_explorer(shapetype,"face")
    
    if face_list:
        common_area = 0
        for common_face in face_list:
            acommon_area = py3dmodel.calculate.face_area(common_face)
            common_area = common_area +  acommon_area
            
        common_ratio = common_area/occ_face_area
        #print "COMMON RATIO:", common_ratio
        if common_ratio >= 0.5:
            return True
        else:
            return False
    else:
        return False
    

def buildings_on_plot(plot_rec, building_list):
    #building_list is a list of dictionary from method get_buildings(shpfile)
    #check which building belongs to this plot
    buildings_on_plot_list = []
    part_list = get_geometry(plot_rec)
    if part_list:
        for part in part_list:
            part3d = point_list2d_2_3d(part,0.0)
            luse_face = py3dmodel.construct.make_polygon(part3d)
    
            for building in building_list:
                geometry_list = building["geometry"]
                for building_face in geometry_list:
                    face_inside = face_almost_inside(building_face, luse_face)
                    if face_inside:
                        buildings_on_plot_list.append(building)
                    
    return buildings_on_plot_list

def get_plot_area(plot_rec):
    plot_area = 0
    part_list = get_geometry(plot_rec)
    if part_list:
        for part in part_list:
            ptlist3d = point_list2d_2_3d(part,0.0)
            luse_face = py3dmodel.construct.make_polygon(ptlist3d)
            plot_area = plot_area + py3dmodel.calculate.face_area(luse_face)
    return plot_area


def building2citygml(building, height, citygml, landuse, storey, epsg):
    yr_construct = "0"
    storey_blw_grd = "0"
    bclass = map_osm2citygml_building_class(landuse)
    if "name" in building:
        name = building["name"]
    else:
        name = "building" + str(uuid.uuid1())
        
    if "amenity" in building:
        function = map_osm2citygml_building_amenity_function(building["amenity"])
    else:
        function = map_osm2citygml_building_function(landuse)
        
    generic_attrib_dict = {"landuse":landuse}
    if "amenity" in building:
        generic_attrib_dict["amenity"] = building["amenity"]
        
    if "parking" in building:
        generic_attrib_dict["parking"] = building["parking"]

    geometry_list = []
    bgeom_list = building["geometry"]
    for bface in bgeom_list:
        #extrude the buildings according to their height
        face_list = gml3dmodel.extrude_building(bface, height)
        #get the surfaces from the solid 
        for face in face_list:
            pt_list = py3dmodel.fetch.pyptlist_frm_occface(face)
            first_pt = pt_list[0]
            pt_list.append(first_pt)
            srf = pycitygml.gmlgeometry.SurfaceMember(pt_list)
            geometry_list.append(srf)
        
    citygml.add_building("lod1", name, bclass, function, function,yr_construct, "1000",str(height),
                         str(storey), storey_blw_grd, epsg, generic_attrib_dict, geometry_list)


def trpst2citygml(trpt_type, rec, name, trpst_attrib, epsg_num, generic_attrib_dict,citygml):
    if name.isspace():
        name = trpst_attrib + str(uuid.uuid1())
    trpst_class = map_osm2citygml_trpst_complex_class(trpst_attrib)
    function = map_osm2citygml_trpst_complex_function(trpst_attrib)
    #get the geometry
    part_list = get_geometry(rec)
    geometry_list = []
    for part in part_list:
        linestring = pycitygml.gmlgeometry.LineString(point_list2d_2_3d(part,0.0))
        geometry_list.append(linestring)
        
    citygml.add_transportation(trpt_type, "lod0", name, trpst_class, function, epsg_num, generic_attrib_dict, geometry_list)
    
def terrain2d23d_tin(terrain_shpfile, elev_attrib_name):
    sf = shapefile.Reader(terrain_shpfile)
    shapeRecs=sf.shapeRecords()
    #shapeRecs = shapeRecs[0:100]
    shapetype = shapeRecs[0].shape.shapeType
    if shapetype !=5:
        raise Exception("this is not a polygonised shpfile")
        
    field_name_list = get_field_name_list(sf)
    elev_index = field_name_list.index(elev_attrib_name)-1
    elev_pts = []

    for rec in shapeRecs:
        poly_attribs=rec.record
        elev = poly_attribs[elev_index]
        part_list = get_geometry(rec)
        #if it is a close the first and the last vertex is the same
        for part in part_list:
            point_list = point_list2d_2_3d(part, elev)
            face = py3dmodel.construct.make_polygon(point_list)
            face_midpt = py3dmodel.calculate.face_midpt(face)
            elev_pts.append(face_midpt)
            
    occtriangles = py3dmodel.construct.delaunay3d(elev_pts)
    return occtriangles
    
def terrain2d23d_contour_line(terrain_shpfile, elev_attrib_name):
    sf = shapefile.Reader(terrain_shpfile)
    shapeRecs=sf.shapeRecords()
    #shapeRecs = shapeRecs[0:10]
    shapetype = shapeRecs[0].shape.shapeType
    if shapetype !=5:
        raise Exception("this is not a polygonised shpfile")
        
    field_name_list = get_field_name_list(sf)
    dn_index = field_name_list.index(elev_attrib_name)-1
    face_list = []
    elev_dict = {}
    for rec in shapeRecs:
        poly_attribs=rec.record
        elev = round(poly_attribs[dn_index], -1)
        if elev not in elev_dict:
            elev_dict[elev] = []
        part_list = get_geometry(rec)
        #if it is a close the first and the last vertex is the same
        for part in part_list:
            point_list = point_list2d_2_3d(part, elev)
            face = py3dmodel.construct.make_polygon(point_list)
            elev_dict[elev].append(face)
            
    for key in elev_dict:
        elev_faces = elev_dict[key]
        merged_faces = py3dmodel.construct.merge_faces(elev_faces)
        face_list.extend(merged_faces)
        
    solid_list = []
    for face in face_list:
        ext_shp = py3dmodel.construct.extrude(face, (0,0,-1), 10)
        ext_solid = py3dmodel.fetch.shape2shapetype(ext_shp)
        solid_list.append(ext_solid)
        
    return solid_list, face_list

def building2d23d(building_shpfile, height_attrib_name, terrain_surface_list):
    sf = shapefile.Reader(building_shpfile)
    shapeRecs=sf.shapeRecords()
    #shapeRecs = shapeRecs[0:10]
    shapetype = shapeRecs[0].shape.shapeType
    if shapetype !=5:
        raise Exception("this is not a polygon building shpfile")
        
    field_name_list = get_field_name_list(sf)
    height_index = field_name_list.index(height_attrib_name)-1
    
    terrainshell = py3dmodel.construct.make_shell_frm_faces(terrain_surface_list)
    terrain_z = []
    for ts in terrain_surface_list:
        vertexes = py3dmodel.fetch.pyptlist_frm_occface(ts)
        for vert in vertexes:
            z = vert[2]
            terrain_z.append(z)
            
    max_z = max(terrain_z)
    min_z = min(terrain_z)
    
    solid_list = []
    for rec in shapeRecs:
        poly_attribs=rec.record
        height = float(poly_attribs[height_index])
        part_list = get_geometry(rec)
        #if it is a close the first and the last vertex is the same
        for part in part_list:
            #create a bounding box to boolean the terrain
            point_list = point_list2d_2_3d(part, (min_z-10))
            face = py3dmodel.construct.make_polygon(point_list)
            bbox = py3dmodel.construct.extrude(face, (0,0,1), (max_z+10))
            bbox_terrain = py3dmodel.fetch.shape2shapetype(py3dmodel.construct.boolean_common(bbox,terrainshell))
            #extract the terrain from in the bbox
            if not py3dmodel.fetch.is_compound_null(bbox_terrain):
                bbox_faces = py3dmodel.fetch.topos_frm_compound(bbox_terrain)["face"]
                midpt_zs = []
                for bbox_face in bbox_faces:
                    bbox_face_midptz = py3dmodel.calculate.face_midpt(bbox_face)[2]
                    midpt_zs.append(bbox_face_midptz)
                belev = max(midpt_zs)
            else:
                belev = 0

            point_list3d = point_list2d_2_3d(part, belev)
            face3d = py3dmodel.construct.make_polygon(point_list3d)
            building_extrude_shp = py3dmodel.construct.extrude(face3d, (0,0,1), height)
            building_extrude_solid = py3dmodel.fetch.shape2shapetype(building_extrude_shp)
            solid_list.append(building_extrude_solid)

    return solid_list