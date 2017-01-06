import os
import time 
import pylibudo

def generate_sensor_surfaces_for_occ_solid(building_solid, xdim, ydim):
    face_list = pylibudo.py3dmodel.fetch.faces_frm_solid(building_solid)
    #loop thru the faces in the solid 
    sensor_pts = []
    sensor_dirs = []
    sensor_srf_list = []
    for f in face_list:
        #generate sensor points for a surface
        a_sensor_srfs, a_sensor_pts, a_sensor_dirs = pylibudo.gml3dmodel.generate_sensor_surfaces(f, xdim, ydim)
        
        if a_sensor_pts != None:
            sensor_pts.extend(a_sensor_pts)
            sensor_dirs.extend(a_sensor_dirs)
            sensor_srf_list.extend(a_sensor_srfs)
            
    return sensor_pts, sensor_dirs, sensor_srf_list
            
def building_solar(building_solids, terrain_faces, weatherfilepath, start_mth, 
                   end_mth, start_day, end_day, start_hour, end_hour, ab, xdim, ydim):

    #parameters for the radiance 
    base_file_path = os.path.join(os.path.dirname(__file__), 'base.rad')
    #TODO: needs to be changed to a better location 
    data_folder_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'py2radiance_data')
    time = str(start_hour) + " " + str(end_hour)
    date = str(start_mth) + " " + str(start_day) + " " + str(end_mth) + " " + str(end_day)
    rad = pylibudo.py2radiance.Rad(base_file_path, data_folder_path)
    
    topo_list = []
    sensor_pts = []
    sensor_dirs = []
    
    bcnt = 0
    for building_solid in building_solids:
        print "BCNT", bcnt
        asensor_pts, asensor_dirs,asensor_surfaces = generate_sensor_surfaces_for_occ_solid(building_solid, xdim, xdim)
        sensor_pts.extend(asensor_pts)
        sensor_dirs.extend(asensor_dirs)
        topo_list.extend(asensor_surfaces)
        
        bface_list = pylibudo.py3dmodel.fetch.faces_frm_solid(building_solid)
        #extract the surfaces from the buildings for shading geometry in radiance
        bf_cnt = 0
        for bface in bface_list:
            bface_pts = pylibudo.py3dmodel.fetch.pyptlist_frm_occface(bface)
            srfname = "building_srf" + str(bcnt) + str(bf_cnt)
            #just use pure white paint
            srfmat = "RAL9010_pur_white_paint"
            pylibudo.py2radiance.RadSurface(srfname, bface_pts, srfmat, rad)
            
            bf_cnt+=1
            
        bcnt+=1
        
    tf_cnt = 0
    for tface in terrain_faces:
        tface_pts = pylibudo.py3dmodel.fetch.pyptlist_frm_occface(tface)
        srfname = "terrain_srf" + str(tf_cnt)
        #just use pure white paint
        srfmat = "RAL9010_pur_white_paint"
        pylibudo.py2radiance.RadSurface(srfname, tface_pts, srfmat, rad)
        tf_cnt+=1
        
    #get the sensor grid points
    rad.set_sensor_points(sensor_pts, sensor_dirs)
    
    #execute radiance cumulative oconv (will create input files for sky and geometry)
    rad.execute_cumulative_oconv(time, date, weatherfilepath)#EXECUTE
                                 
    #execute cumulative_rtrace
    rad.execute_cumulative_rtrace(str(ab))#EXECUTE!! 
    #retrieve the results
    irrad_res = rad.eval_cumulative_rad()
    return topo_list, irrad_res
    
#============================================================================================================================
#main script
#============================================================================================================================
    #not for public
time1 = time.clock()
display2dlist = []
colour_list = []

print "CALCULATING TERRAIN"
poly_path = "F:\\kianwee_work\\smart\\oct2015-apr2016\\for_jimeno_shp2solar\\KianWee_material\\files\\terrain_polygonised.gml\\terrain_polygonised.shp"
terrain_triangles = pylibudo.shp2citygml.terrain2d23d_tin(poly_path, "DN")
display2dlist.append(terrain_triangles)
colour_list.append("WHITE")
#display the edges of the terrain
tedges = []
for t in terrain_triangles:
    twire = pylibudo.py3dmodel.fetch.wires_frm_face(t)[0]
    tedge = pylibudo.py3dmodel.fetch.edges_frm_wire(twire)
    tedges.extend(tedge)
    
display2dlist.append(tedges)
colour_list.append("BLACK")

time2 = time.clock()
terrain_time = (time2-time1)/60
print "DONE WITH TERRAIN"
print "TERRAIN TIME", terrain_time

print "CALCULATING BUILDINGS"
building_shpfile = "F:\\kianwee_work\\smart\\oct2015-apr2016\\for_jimeno_shp2solar\\KianWee_material\\files\\Buildings.shp"
bsolids = pylibudo.shp2citygml.building2d23d(building_shpfile, "Height_ag", terrain_triangles)
#369 buildings
time3 = time.clock()
building_time = (time3-time2)/60
print "DONE WITH BUILDING"
print "BUILDING TIME", building_time

print "RADIANCE EVALUATING"
xdim = 10
ydim = 10
weatherfilepath = "F:\\kianwee_work\\smart\\oct2015-apr2016\\for_jimeno_shp2solar\\KianWee_material\\weather_data\\hochshculQuartier-Zurich-hour.epw"
latitude = 47.3667
longtitude = 8.5500
meridian = 10
start_mth = 1
end_mth = 12
start_day = 1
end_day = 31
start_hour = 7
end_hour = 19
ab = 2

topo_list, irrad_res = building_solar(bsolids, terrain_triangles, weatherfilepath, start_mth, 
                                      end_mth, start_day, end_day, start_hour, end_hour, ab, xdim, ydim)

time4 = time.clock()
radiance_time = time4-time3

total_time = (time4-time1)/60
print "TOTAL TIME", total_time

print "VISUALISING"
falsecolour_file ="F:\\kianwee_work\\spyder_workspace\\py2radiance_data\\falsecolour.png"
image_file = "F:\\kianwee_work\\spyder_workspace\\py2radiance_data\\result.png"

pylibudo.py3dmodel.construct.visualise_falsecolour_topo(irrad_res, topo_list, falsecolour_file, image_file, display2dlist, colour_list)
