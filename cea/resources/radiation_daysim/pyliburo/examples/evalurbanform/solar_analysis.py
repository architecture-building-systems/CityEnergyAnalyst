import pyliburo
from collada import *

dae_file = "F:\\kianwee_work\\smart\\case_studies\\5x5ptblks\\dae\\5x5ptblks.dae"
weatherfilepath = "F:\\kianwee_work\\spyder_workspace\\pyliburo\\examples\\punggol_case_study\\weatherfile\\SGP_Singapore.486980_IWEC.epw"
rad_filepath = "F:\\kianwee_work\\smart\\case_studies\\5x5ptblks\\py2radiance_dfavi"
daysim_filepath = "F:\\kianwee_work\\smart\\case_studies\\5x5ptblks\\daysim_data"

def read_collada(dae_filepath):
    buildinglist = []
    luselist = []
    mesh = Collada(dae_file)
    unit = mesh.assetInfo.unitmeter or 1
    geoms = mesh.scene.objects('geometry')
    geoms = list(geoms)
    gcnt = 0
    for geom in geoms:   
        prim2dlist = list(geom.primitives())
        for primlist in prim2dlist:  
            buildinglist.append([])
            if primlist:
                for prim in primlist:
                    if type(prim) == polylist.Polygon or type(prim) == triangleset.Triangle:
                        pyptlist = prim.vertices.tolist()
                        occpolygon = pyliburo.py3dmodel.construct.make_polygon(pyptlist)
                        pyliburo.py3dmodel.fetch.is_face_null(occpolygon)
                        if not pyliburo.py3dmodel.fetch.is_face_null(occpolygon):
                            if gcnt == 550:#the last geometry is the plot
                                luselist.append(occpolygon)
                            else:
                                buildinglist[-1].append(occpolygon)
                            gcnt +=1
                  
    #create solid out of the buildings 
    shapelist = []
    for bfaces in buildinglist:
        if bfaces:                
            bsolid = pyliburo.py3dmodel.construct.make_solid(pyliburo.py3dmodel.construct.make_shell_frm_faces(bfaces)[0])    
            shapelist.append(bsolid)

    shapelist.extend(luselist)
    compound = pyliburo.py3dmodel.construct.make_compound(shapelist)  
    ref_pt = pyliburo.py3dmodel.calculate.face_midpt(luselist[0])
    scaled_shape = pyliburo.py3dmodel.modify.uniform_scale(compound, unit, unit, unit,ref_pt)
    scaled_compound = pyliburo.py3dmodel.fetch.shape2shapetype(scaled_shape)
    solid_list = redraw_occfaces(scaled_compound)
    return solid_list
    
def redraw_occfaces(occcompound):
    #redraw the surfaces so the domain are right
    #TODO: fix the scaling 
    solids = pyliburo.py3dmodel.fetch.geom_explorer(occcompound, "solid")
    solidlist = []
    for solid in solids:
        faces = pyliburo.py3dmodel.fetch.geom_explorer(solid, "face")
        recon_faces = []
        for face in faces:
            pyptlist = pyliburo.py3dmodel.fetch.pyptlist_frm_occface(face)
            recon_face = pyliburo.py3dmodel.construct.make_polygon(pyptlist)
            recon_faces.append(recon_face)
        recon_shell = pyliburo.py3dmodel.construct.make_shell_frm_faces(recon_faces)[0]
        recon_solid = pyliburo.py3dmodel.construct.make_solid(recon_shell)
        solidlist.append(recon_solid)
    return solidlist
    
collada_solids = read_collada(dae_file)
collada_solids = collada_solids[0:3]

#==========================================================================================================================
#SHGFAVI
#==========================================================================================================================

#irrad_threshold (kwh/m2)
#50w/m2 is the benchmark envelope thermal transfer value for spore greenmark basic for commercial buildings
#its calculated as an hourly average, multiplying it by 8760 hrs, we get the rough value for the permissible annual solar heat gain
#1.5 is a factor to account for the raw irradiation falling on the surface, the higher we assume the better your envelope quality. 
#factor of 1.5 means we expect 60% of the heat to be transmitted through the envelope 


irrad_threshold = (50*8760*1.5)/1000.0
avg_shgfavi, shgfavi_percent, shgfai, topo_list, irrad_ress = pyliburo.urbanformeval.shgfavi(collada_solids, irrad_threshold, 
                                                                                     weatherfilepath, 10,10, rad_filepath )
print avg_shgfavi, shgfai

#==========================================================================================================================
#DFAVI
#==========================================================================================================================
illum_threshold = 10000
avg_dfavi, dfavi_percent, dfai, topo_list, illum_ress = pyliburo.urbanformeval.dfavi(collada_solids, illum_threshold, 
                                                                                     weatherfilepath, 10,10, 
                                                                                     rad_filepath, daysim_filepath )

print avg_dfavi, dfai

#==========================================================================================================================
#PVAVI
#==========================================================================================================================
pv_facade_threshold = 512 #kwh/m2
pv_roof_threshold = 1280 #kwh/m2

avg_pvfavi, pvavi_percent, pvfai, epv, topo_list, irrad_ress =  pyliburo.urbanformeval.pvavi(collada_solids, 
                                                                                                  pv_facade_threshold, 
                                                                                                  weatherfilepath, 10, 10, 
                                                                                                  rad_filepath, 
                                                                                                  mode = "facade",
                                                                                                  pvavi_threshold = None)
                                                                                                  
print avg_pvfavi, pvfai

                                                                                               
avg_pvfavi, pvavi_percent, pvfai, epv, topo_list, irrad_ress = pyliburo.urbanformeval.pveavi(collada_solids, 
                                                                                             pv_roof_threshold, 
                                                                                             pv_facade_threshold, 
                                                                                             weatherfilepath, 10, 10, 
                                                                                             rad_filepath, 
                                                                                             pvravi_threshold = None, 
                                                                                             pvfavi_threshold = None, 
                                                                                             pveavi_threshold = None)
                                                                                             
print avg_pvfavi, pvfai

pyliburo.py3dmodel.construct.visualise_falsecolour_topo(irrad_ress, topo_list)