import pyliburo
from collada import *

dae_file = "F:\\kianwee_work\\spyder_workspace\\pyliburo\\examples\\punggol_case_study\\collada\\simple_case_connectivity.dae"
                    
def read_collada(dae_filepath):
    plots_occfacelist = []
    network_occedgelist = []
    buildinglist = []
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
                        if not pyliburo.py3dmodel.fetch.is_face_null(occpolygon):
                            plots_occfacelist.append(occpolygon)
                            gcnt +=1
                    elif type(prim) == lineset.Line:
                        pyptlist = prim.vertices.tolist()
                        occedge = pyliburo.py3dmodel.construct.make_edge(pyptlist[0], pyptlist[1])
                        network_occedgelist.append(occedge)
                        gcnt +=1
                  
    #create solid out of the buildings 
    compound1 = pyliburo.py3dmodel.construct.make_compound(plots_occfacelist)  
    compound2 = pyliburo.py3dmodel.construct.make_compound(network_occedgelist)  
    
    ref_pt = pyliburo.py3dmodel.calculate.face_midpt(plots_occfacelist[0])
    scaled_shape1 = pyliburo.py3dmodel.modify.uniform_scale(compound1, unit, unit, unit,ref_pt)
    scaled_shape2 = pyliburo.py3dmodel.modify.uniform_scale(compound2, unit, unit, unit,ref_pt)
    scaled_compound1 = pyliburo.py3dmodel.fetch.shape2shapetype(scaled_shape1)
    scaled_compound2 = pyliburo.py3dmodel.fetch.shape2shapetype(scaled_shape2)
    
    recon_faces1, recon_edges1 = redraw_occfaces(scaled_compound1)
    recon_faces2, recon_edges2 = redraw_occfaces(scaled_compound2)
    
    return recon_faces1, recon_edges2
    
def redraw_occfaces(occcompound):
    #redraw the surfaces so the domain are right
    #TODO: fix the scaling 
    faces = pyliburo.py3dmodel.fetch.geom_explorer(occcompound, "face")
    recon_faces = []
    for face in faces:
        pyptlist = pyliburo.py3dmodel.fetch.pyptlist_frm_occface(face)
        recon_face = pyliburo.py3dmodel.construct.make_polygon(pyptlist)
        recon_faces.append(recon_face)
        
    edges = pyliburo.py3dmodel.fetch.geom_explorer(occcompound, "edge")
    recon_edges = []
    for edge in edges:
        eptlist = pyliburo.py3dmodel.fetch.points_from_edge(edge)
        epyptlist = pyliburo.py3dmodel.fetch.occptlist2pyptlist(eptlist)
        recon_edges.append(pyliburo.py3dmodel.construct.make_edge(epyptlist[0], epyptlist[1]))
        
    return recon_faces, recon_edges
    
plots_occfacelist, network_occedgelist  = read_collada(dae_file)

#find the boundary surface: the surface with the biggest area
plot_arealist = []
plot_wirelist = []

for pf in plots_occfacelist:
    parea = pyliburo.py3dmodel.calculate.face_area(pf)
    plot_arealist.append(parea)
    plot_wire = pyliburo.py3dmodel.fetch.wires_frm_face(pf)
    plot_wirelist.extend(plot_wire)
    
boundary_area = max(plot_arealist) 
boundary_index = plot_arealist.index(boundary_area)
boundary_occface = plots_occfacelist[boundary_index]
plots_occfacelist.remove(boundary_occface)

avg_rdi,rdi_per,plts,passplts,failplts,rdi_list,edges,peri  = pyliburo.urbanformeval.route_directness(network_occedgelist, 
                                                                                                         plots_occfacelist, 
                                                                                                         boundary_occface, 
                                                                                                    route_directness_threshold = 4)
                                                                                                    
print rdi_per, avg_rdi
print rdi_list
display2dlist = []
display2dlist.append(edges + peri )
colourlist = ["WHITE", "RED", 'BLACK']
#display2dlist.append(passplts)
#display2dlist.append(failplts)
#pyliburo.py3dmodel.construct.visualise(display2dlist, colourlist)
pyliburo.py3dmodel.construct.visualise_falsecolour_topo(rdi_list,plts, other_topo2dlist=display2dlist,
                                                        other_colourlist = colourlist, maxval_range = 4)