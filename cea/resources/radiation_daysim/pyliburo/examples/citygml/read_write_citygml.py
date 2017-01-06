import os
import time
import pyliburo

#specify the citygml file
current_path = os.path.dirname(__file__)
parent_path = os.path.abspath(os.path.join(current_path, os.pardir))
citygml_filepath = os.path.join(parent_path, "punggol_case_study", "citygml", "punggol_citygml.gml")
print "READING CITYGML FILE ... ..."

time1 = time.clock()
#===================================================================================================
#read the citygml file 
#===================================================================================================
read_citygml = pyliburo.pycitygml.Reader(citygml_filepath)
buildings = read_citygml.get_buildings()
landuses = read_citygml.get_landuses()
stops = read_citygml.get_bus_stops()
roads = read_citygml.get_roads()
railways = read_citygml.get_railways()

#get all the polylines of the lod0 roads
for road in roads:
    polylines = read_citygml.get_linestring(road)

#get all the polygons of the landuses
for landuse in landuses:
    polygons = read_citygml.get_polygons(landuse)
    
#get all the stations in the buildings and extract their polygons 
stations = []
for building in buildings:
    bclass = building.find("bldg:class", namespaces=read_citygml.namespaces).text
    bfunction = building.find("bldg:function", namespaces=read_citygml.namespaces).text
    
    if bclass == "1170" and bfunction == "2480":
        stations.append(building)
    polygons = read_citygml.get_polygons(building)
    for polygon in polygons:
        polygon_id = polygon.attrib["{%s}id" % read_citygml.namespaces['gml']]
        pos_list = read_citygml.get_poslist(polygon)
       
print "SORTING CITYGML FILE ... ..."
#===================================================================================================
#get a specific plot of landuse and the buildings on the plot
#===================================================================================================
landuses = landuses[5:6]
pylanduse_polygons = []
pybuilding_polygons = []

#extract all the footprint of the buildings 
building_footprints = []
for building in buildings:
    footprint_dict = {}
    pypolygon_list = read_citygml.get_pypolygon_list(building)
    solid = pyliburo.threedmodel.pypolygons2occsolid(pypolygon_list)
    face_list = pyliburo.py3dmodel.fetch.faces_frm_solid(solid)
    for face in face_list:
        normal = pyliburo.py3dmodel.calculate.face_normal(face)
        if normal == (0,0,-1):
            fpt_list = pyliburo.py3dmodel.fetch.pyptlist_frm_occface(face)
            
    footprint_dict["footprint"] = fpt_list
    footprint_dict["building"] = building
    building_footprints.append(footprint_dict)
    
#find all the buildings inside the landuse 
buildings2write = []
for landuse in landuses:
    lpolygon = read_citygml.get_polygons(landuse)[0]
    landuse_pts = read_citygml.polygon_2_pt_list(lpolygon)
    
    lface = pyliburo.py3dmodel.construct.make_polygon(landuse_pts)
    pylanduse_polygons.append(landuse_pts)
    
    buildings_on_plot_list = []
    
    for bf in building_footprints:
        fp = bf["footprint"]
        cbuilding = bf["building"]
        fface = pyliburo.py3dmodel.construct.make_polygon(fp)
        if pyliburo.py3dmodel.calculate.face_is_inside(fface, lface):
            buildings_on_plot_list.append(cbuilding)
            
    #get the solid of each building on the plot
    for building in buildings_on_plot_list:
        pypolgon_list = read_citygml.get_pypolygon_list(building)
        solid = pyliburo.threedmodel.pypolygons2occsolid(pypolgon_list)
        pybuilding_polygons.append(pypolgon_list)
        buildings2write.append(building)
        
#===================================================================================================
#only write the specific plot and the buildings into a new citygml file
#write the citygml from scratch 
#===================================================================================================
print "WRITING CITYGML FILE ... ..."
result_citygml_filepath = os.path.join(parent_path, "punggol_case_study", "citygml", "punggol_luse5.gml")
citygml_writer = pyliburo.pycitygml.Writer()
luse_cnt = 0
for luse in landuses:
    luse_lod = "lod1"
    luse_name = read_citygml.get_landuse_name(luse)
    luse_function = read_citygml.get_landuse_function(luse)
    luse_epsg = read_citygml.get_epsg(luse)
    luse_generic_attrib_dict = read_citygml.get_generic_attribs(luse)
    luse_geometry_list = []
    
    for pypoly in pylanduse_polygons:
        gml_srf = pyliburo.pycitygml.gmlgeometry.SurfaceMember(pypoly)
        luse_geometry_list.append(gml_srf)
    
    citygml_writer.add_landuse(luse_lod, luse_name, luse_function, luse_epsg, luse_generic_attrib_dict, luse_geometry_list)
    luse_cnt +=1

bldg_cnt = 0
for building in buildings2write:
    bldg_lod = "lod1"
    bldg_name = read_citygml.get_gml_id(building)
    bldg_class = read_citygml.get_building_class(building)
    bldg_function = read_citygml.get_building_function(building)
    bldg_usage = read_citygml.get_building_usage(building)
    bldg_yr_construct = read_citygml.get_building_yr_constr(building)
    bldg_rooftype = read_citygml.get_building_rooftype(building)
    bldg_height = read_citygml.get_building_height(building)
    bldg_str_abv_grd = read_citygml.get_building_storey(building)
    bldg_str_blw_grd = read_citygml.get_building_storey_blw_grd(building)
    bldg_epsg = read_citygml.get_epsg(building)
    bldg_generic_attrib_dict = read_citygml.get_generic_attribs(building)
    bldg_geometry_list = []
    for pypoly in pybuilding_polygons[bldg_cnt]:
        gml_srf = pyliburo.pycitygml.gmlgeometry.SurfaceMember(pypoly)
        bldg_geometry_list.append(gml_srf)
    
    citygml_writer.add_building(bldg_lod, bldg_name, bldg_class, bldg_function, bldg_usage,bldg_yr_construct,bldg_rooftype,str(bldg_height),str(bldg_str_abv_grd),
                   str(bldg_str_blw_grd), bldg_epsg, bldg_generic_attrib_dict, bldg_geometry_list)
                   
    bldg_cnt +=1
    
citygml_writer.write(result_citygml_filepath)
time2 = time.clock()
time = (time2-time1)/60.0
print "TIME TAKEN", time
print "CITYGML FILE GENERATED"