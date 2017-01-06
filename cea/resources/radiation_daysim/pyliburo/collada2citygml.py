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
from collada import *

'''
script to automatically convert a collada file into citygml file
the script is tested with a collada file exported from sketchup
'''

def daesrfs2occsrfs(daefacelist):
    occfacelist = []
    for face in daefacelist:
        pyptlist = face.vertices.tolist()
        occface = py3dmodel.construct.make_polygon(pyptlist)
        occfacelist.append(occface)
        
    return occfacelist
                    
def daeedges2occedges(daeedgelist):
    occedgelist = []
    for edge in daeedgelist:
        pyptlist = edge.vertices.tolist()
        occedge = py3dmodel.construct.make_edge(pyptlist[0], pyptlist[1])
        occedgelist.append(occedge)
            
    return occedgelist
    
def edges3d22d(occedgelist):
    occedge2d_list = []
    for edge in occedgelist:
        occptlist = py3dmodel.fetch.points_from_edge(edge)
        pyptlist = py3dmodel.fetch.occptlist2pyptlist(occptlist)
        pyptlist2d = []
        for pypt in pyptlist:
            pypt2d = (pypt[0], pypt[1],0)
            pyptlist2d.append(pypt2d)
        occedge2d = py3dmodel.construct.make_edge(pyptlist2d[0], pyptlist2d[1])
        occedge2d_list.append(occedge2d)
    return occedge2d_list

def wire3d22d(occwire):
    pyptlist2d = []
    pyptlist = py3dmodel.fetch.occptlist2pyptlist(py3dmodel.fetch.points_frm_wire(occwire))
    
    for pypt in pyptlist:
        pypt2d = [pypt[0],pypt[1],0]
        pyptlist2d.append(pypt2d)
         
    pyptlist2d.append(pyptlist2d[0])
    occwire2d = py3dmodel.construct.make_wire(pyptlist2d)
    return occwire2d
    
def sphere2edge_pts(occedgelist, radius):
    circlelist = []
    for edge in occedgelist:
        occptlist = py3dmodel.fetch.points_from_edge(edge)
        pyptlist = py3dmodel.fetch.occptlist2pyptlist(occptlist)
        for pypt in pyptlist:
            occcircle = py3dmodel.construct.make_circle(pypt, (0,0,1), radius)
            circlelist.append(occcircle)
    return circlelist
    
def consolidate_terrain_shelllist(terrain_shelllist):
    terrain_faces = []
    for shell in terrain_shelllist:
        terrain_faces.extend(py3dmodel.fetch.faces_frm_shell(shell))
        
    consolidated_terrain_shelllist = py3dmodel.construct.make_shell_frm_faces(terrain_faces)
    return consolidated_terrain_shelllist

def is_edge_touching_terrain(edgelist, terrain_shelllist):
    touchlist = []
    min_dislist = []
    for shell in terrain_shelllist:
        for edge in edgelist:
            min_dist = py3dmodel.calculate.minimum_distance(edge, shell)
            min_dislist.append(min_dist)
            if round(min_dist,6) == 0:
                touchlist.append(1)
                
    if len(touchlist) >= len(edgelist):
        return True
    else:
        return False
#==============================================================================================================        
#==============================================================================================================
def redraw_occ_shell_n_edge(occcompound):
    #redraw the surfaces so the domain are right
    #TODO: fix the scaling 
    recon_shelllist = []
    shells = py3dmodel.fetch.geom_explorer(occcompound, "shell")
    for shell in shells:
        faces = py3dmodel.fetch.geom_explorer(shell, "face")
        recon_faces = []
        for face in faces:
            pyptlist = py3dmodel.fetch.pyptlist_frm_occface(face)
            recon_face = py3dmodel.construct.make_polygon(pyptlist)
            recon_faces.append(recon_face)
        nrecon_faces = len(recon_faces)
        if nrecon_faces == 1:
            recon_shell = py3dmodel.construct.make_shell(recon_faces)
        if nrecon_faces > 1:
            recon_shell = py3dmodel.construct.make_shell_frm_faces(recon_faces)[0]
        recon_shelllist.append(recon_shell)
        
    #boolean the edges from the shell compound and edges compound and find the difference to get the network edges
    shell_compound = py3dmodel.construct.make_compound(shells)
    shell_edges = py3dmodel.fetch.geom_explorer(shell_compound, "edge")
    shell_edge_compound = py3dmodel.construct.make_compound(shell_edges)
    
    edges = py3dmodel.fetch.geom_explorer(occcompound, "edge")
    edge_compound = py3dmodel.construct.make_compound(edges)
    network_edge_compound = py3dmodel.construct.boolean_difference(edge_compound,shell_edge_compound) 
    
    nw_edges = py3dmodel.fetch.geom_explorer(network_edge_compound,"edge")
    recon_edgelist = []
    for edge in nw_edges:
        eptlist = py3dmodel.fetch.points_from_edge(edge)
        epyptlist = py3dmodel.fetch.occptlist2pyptlist(eptlist)
        recon_edgelist.append(py3dmodel.construct.make_edge(epyptlist[0], epyptlist[1]))
        
    recon_compoundlist = recon_shelllist + recon_edgelist
    recon_compound = py3dmodel.construct.make_compound(recon_compoundlist)
    return recon_compound
    
def simplify_shell(occshell):
    #this will merge any coincidental faces into a single surfaces to simplify the geometry
    fshell = py3dmodel.modify.fix_shell_orientation(occshell)
    #get all the faces from the shell and arrange them according to their normals
    sfaces = py3dmodel.fetch.geom_explorer(fshell,"face")
    nf_dict = py3dmodel.calculate.grp_faces_acc2normals(sfaces)
    merged_fullfacelist = []
    #merge all the faces thats share edges into 1 face
    for snfaces in nf_dict.values():
        merged_facelist = py3dmodel.construct.merge_faces(snfaces)
        merged_fullfacelist.extend(merged_facelist)
        
    if len(merged_fullfacelist) >1:
        simpleshell = py3dmodel.construct.make_shell_frm_faces(merged_fullfacelist)
        fshell2 = py3dmodel.modify.fix_shell_orientation(simpleshell[0])
        
    else:
        #if there is only one face it means its an open shell
        fshell2 = py3dmodel.construct.make_shell(merged_fullfacelist)
    return fshell2

def make_2dboundingface(occshape):
    xmin,ymin,zmin,xmax,ymax,zmax = py3dmodel.calculate.get_bounding_box(occshape)
    boundary_pyptlist = [[xmin,ymin,0], [xmax,ymin,0], [xmax,ymax,0], [xmin,ymax,0]]
    boundary_face = py3dmodel.construct.make_polygon(boundary_pyptlist)
    return boundary_face
    
def identify_shell_attribs(occshelllist):
    nshells = len(occshelllist)
    shell_dictlist = []

    for shellcnt in range(nshells):
        shell_dict = {}
        is_in_boundary = []
        boundary_contains = []
        #first check if it is an open or close shell
        shell = occshelllist[shellcnt]
        shell_dict["shell"] = shell
        is_closed = py3dmodel.calculate.is_shell_closed(shell)
        if is_closed:
            shell_dict["is_closed"] = True
        else:
            shell_dict["is_closed"] = False
        cur_boundary = make_2dboundingface(shell)
        for shellcnt2 in range(nshells):
            if shellcnt2 != shellcnt:
                nxt_shell = occshelllist[shellcnt2]
                nxt_boundary = make_2dboundingface(nxt_shell)
                #check if cur_shell is inside nxt_shell
                is_inside_nxt_boundary = py3dmodel.calculate.face_is_inside(cur_boundary,nxt_boundary)
                if is_inside_nxt_boundary:
                    is_in_boundary.append(nxt_shell)
                    
                #check if cur_shell contains nxt_shell
                contains_nxt_boundary = py3dmodel.calculate.face_is_inside(nxt_boundary,cur_boundary)
                if contains_nxt_boundary:
                    boundary_contains.append(nxt_shell)
                    
        shell_dict["is_in_boundary"] = is_in_boundary
        shell_dict["boundary_contains"] = boundary_contains
        shell_dictlist.append(shell_dict)
    return shell_dictlist
    
def identify_edge_attribs(occedgelist, occshelllist):
    edge_dictlist = []
    for edge in occedgelist:
        edge_dict = {}
        is_in_boundary = []
        edge_dict["edge"] = edge
        for shell in occshelllist:
            min_dist = py3dmodel.calculate.minimum_distance(edge,shell)
            if min_dist < 0.0001:
                is_in_boundary.append(shell)
                
        edge_dict["is_in_boundary"] = is_in_boundary
        edge_dictlist.append(edge_dict)
    return edge_dictlist
    
def read_collada(dae_filepath):
    edgelist = []
    shelllist = []
    mesh = Collada(dae_filepath)
    unit = mesh.assetInfo.unitmeter or 1
    geoms = mesh.scene.objects('geometry')
    geoms = list(geoms)
    gcnt = 0
    for geom in geoms:   
        prim2dlist = list(geom.primitives())
        for primlist in prim2dlist: 
            spyptlist = []
            epyptlist = []
            faces = []
            edges = []
            if primlist:
                for prim in primlist:
                    if type(prim) == polylist.Polygon or type(prim) == triangleset.Triangle:
                        pyptlist = prim.vertices.tolist()
                        pyptlist.sort()
                        if pyptlist not in spyptlist:
                            spyptlist.append(pyptlist)
                            occpolygon = py3dmodel.construct.make_polygon(pyptlist)
                            if not py3dmodel.fetch.is_face_null(occpolygon):
                                faces.append(occpolygon)
                            gcnt +=1
                    elif type(prim) == lineset.Line:
                        pyptlist = prim.vertices.tolist()
                        pyptlist.sort()
                        if pyptlist not in epyptlist:
                            epyptlist.append(pyptlist)
                            occedge = py3dmodel.construct.make_edge(pyptlist[0], pyptlist[1])
                            edges.append(occedge)
                        gcnt +=1
                        
                if faces:
                    #remove all the duplicated faces
                    #non_dup_faces = py3dmodel.modify.rmv_duplicated_faces(faces)
                    n_unique_faces = len(faces)
                    if n_unique_faces == 1:
                        shell = py3dmodel.construct.make_shell(faces)
                        shelllist.append(shell)
                    if n_unique_faces >1:
                        shell = py3dmodel.construct.make_shell_frm_faces(faces)[0]
                        #this will merge any coincidental faces into a single surfaces to simplify the geometry
                        shell = simplify_shell(shell)
                        shelllist.append(shell)
                else:
                    edgelist.extend(edges)
    
    #find the midpt of all the geometry
    compoundlist = shelllist + edgelist
    compound = py3dmodel.construct.make_compound(compoundlist)
    xmin,ymin,zmin,xmax,ymax,zmax = py3dmodel.calculate.get_bounding_box(compound)
    ref_pt = py3dmodel.calculate.get_centre_bbox(compound)
    ref_pt = (ref_pt[0],ref_pt[1],zmin)
    #make sure no duplicate edges 
    scaled_shape = py3dmodel.modify.uniform_scale(compound, unit, unit, unit,ref_pt)
    scaled_compound = py3dmodel.fetch.shape2shapetype(scaled_shape)
    recon_compound = redraw_occ_shell_n_edge(scaled_compound)

    return recon_compound
    
def identify_cityobj(occcompound):
    cityobj_dict = {}
    building_list = []
    landuse_list = []
    terrain_list = []
    network_list = []
    
    #define the geometrical attributes between shells
    shells  = py3dmodel.fetch.geom_explorer(occcompound,"shell")
    shell_dict_list = identify_shell_attribs(shells)
    
    #boolean the edges from the shell compound and edges compound and find the difference to get the network edges
    shell_compound = py3dmodel.construct.make_compound(shells)
    shell_edges = py3dmodel.fetch.geom_explorer(shell_compound, "edge")
    shell_edge_compound = py3dmodel.construct.make_compound(shell_edges)
    
    edges = py3dmodel.fetch.geom_explorer(occcompound, "edge")
    edge_compound = py3dmodel.construct.make_compound(edges)
    network_edge_compound = py3dmodel.construct.boolean_difference(edge_compound,shell_edge_compound) 
    nw_edges = py3dmodel.fetch.geom_explorer(network_edge_compound,"edge")
    #define the geometrical attributes between edges and shells    
    edge_dict_list = identify_edge_attribs(nw_edges, shells)
    
    for shell_dict in shell_dict_list:
        shell = shell_dict["shell"]
        is_closed = shell_dict["is_closed"]
        is_in_boundary = shell_dict["is_in_boundary"]
        boundary_contains = shell_dict["boundary_contains"]
        if is_closed == True and len(is_in_boundary)>0 and len(boundary_contains) == 0:
            building_list.append(shell)
        if is_closed == False and len(is_in_boundary)==0 and len(boundary_contains)> 0:
            terrain_list.append(shell)
        if is_closed == False and len(is_in_boundary)>0 and len(boundary_contains)> 0:
            landuse_list.append(shell)
    
    for edge_dict in edge_dict_list:
        edge = edge_dict["edge"]
        is_in_boundary = edge_dict["is_in_boundary"]
        if len(is_in_boundary) >0:
            network_list.append(edge)
            
    cityobj_dict["building"] = building_list
    cityobj_dict["landuse"] = landuse_list
    cityobj_dict["terrain"] = terrain_list
    cityobj_dict["network"] = network_list
    return cityobj_dict
        
def auto_convert_dae2gml(colladafile):
    dae_compound = read_collada(colladafile)
    cityobj_dict = identify_cityobj(dae_compound)
    return cityobj_dict
    
'''
def convert(collada_file):
    dae = Collada(collada_file)
    nodes = dae.scene.nodes
    
    #this loops thru the visual scene 
    #loop thru the library nodes
    for node in nodes:
        name = node.xmlnode.get('name')
        children_nodes = node.children
        if children_nodes:
            for node2 in children_nodes:
                name2 = node2.xmlnode.get('name')
                print 'name2', name2
                children_node2 = node2.children
                if children_node2:
                    if type(children_node2[0]) == scene.NodeNode:
                        print children_node2[0].children

    
    meshs = list(dae.scene.objects('geometry')) 
    geomlist = []
    meshcnt = 0
    for mesh in meshs:
        prim2dlist = list(mesh.primitives())
        for primlist in prim2dlist:     
            if primlist:
                geom_dict = {}
                geom_dict["meshcnt"] = meshcnt
                if type(primlist) == triangleset.BoundTriangleSet or type(primlist) == polylist.BoundPolylist:
                    #need to check if the triangleset is a close solid 
                    occfacelist = daesrfs2occsrfs(primlist)
                    occshell = py3dmodel.construct.make_shell_frm_faces(occfacelist)[0]
                    shell_closed = py3dmodel.calculate.is_shell_closed(occshell)
                    if shell_closed:#solids are possibly building massings
                        merged_fullfacelist = []
                        #group the faces according to their normals
                        occfacelist = py3dmodel.fetch.faces_frm_shell(occshell)
                        nf_dict = py3dmodel.calculate.grp_faces_acc2normals(occfacelist)
                        #merge all the faces thats share edges into 1 face
                        for faces in nf_dict.values():
                            merged_facelist = py3dmodel.construct.merge_faces(faces)
                            merged_fullfacelist.extend(merged_facelist)
                        shell = py3dmodel.construct.make_shell_frm_faces(merged_fullfacelist)[0]
                        solid = py3dmodel.construct.make_solid(shell)
                        geom_dict["solidorshell"] = solid
                        geom_dict["is_solid"] = True
                            
                    elif not shell_closed: #open shells are possibly terrains and plots
                        geom_dict["solidorshell"] = occshell
                        geom_dict["is_solid"] = False

                elif type(primlist) == lineset.BoundLineSet: 
                    occedgelist = daeedges2occedges(primlist)
                    geom_dict["edgelist"] = occedgelist
                    
                geomlist.append(geom_dict)
                
        meshcnt +=1
        
    #first find which of the open shell is a terrain
    cityobject_dict = identify_city_objects(geomlist)
    
    return cityobject_dict
'''