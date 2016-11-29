from OCCUtils import Topology
from OCC.BRep import BRep_Tool
from OCC.TopExp import TopExp_Explorer
from OCC.TopAbs import TopAbs_COMPOUND, TopAbs_COMPSOLID, TopAbs_SOLID, TopAbs_SHELL, TopAbs_FACE, TopAbs_WIRE, TopAbs_EDGE, TopAbs_VERTEX
from OCC.TopoDS import topods_Compound, topods_CompSolid, topods_Solid, topods_Shell, topods_Face, topods_Wire, topods_Edge, topods_Vertex

def vertex2point(occ_vertex):
    occ_pnt = BRep_Tool.Pnt(occ_vertex)
    return occ_pnt

def vertex_list_2_point_list(occ_vertex_list):
    point_list = []
    for vert in occ_vertex_list:
        point_list.append(BRep_Tool.Pnt(vert))
    return point_list

def shape2shapetype(occ_shape):
    shapetype = occ_shape.ShapeType()
    if shapetype == 0:#compound
        orig_topo = topods_Compound(occ_shape)
    if shapetype == 1:#compsolid
        orig_topo = topods_CompSolid(occ_shape)
    if shapetype == 2:#solid
        orig_topo = topods_Solid(occ_shape)
    if shapetype == 3:#shell
        orig_topo = topods_Shell(occ_shape)
    if shapetype == 4:#face
        orig_topo = topods_Face(occ_shape)
    if shapetype == 5:#wire
        orig_topo = topods_Wire(occ_shape)
    if shapetype == 6:#edge
        orig_topo = topods_Edge(occ_shape)
    if shapetype == 7:#vertex
        orig_topo = topods_Vertex(occ_shape)
    return orig_topo

def geom_explorer(geom2explore, shapetype2find_topABS):
    geom_list = []
    ex = TopExp_Explorer(geom2explore, shapetype2find_topABS)
    while ex.More():
        if shapetype2find_topABS == 0:
            geom = topods_Compound(ex.Current())
        if shapetype2find_topABS == 1:
            geom = topods_CompSolid(ex.Current())
        if shapetype2find_topABS == 2:
            geom = topods_Solid(ex.Current())
        if shapetype2find_topABS == 3:
            geom = topods_Shell(ex.Current())
        if shapetype2find_topABS == 4:
            geom = topods_Face(ex.Current())
        if shapetype2find_topABS == 5:
            geom = topods_Wire(ex.Current())
        if shapetype2find_topABS == 6:
            geom = topods_Edge(ex.Current())
        if shapetype2find_topABS == 7:
            geom = topods_Vertex(ex.Current())
        geom_list.append(geom)
        ex.Next()
    return geom_list

def topos_frm_compound(occ_compound):
    topo_list = {}
    
    #find all the compsolids
    compsolid_list = geom_explorer(occ_compound, TopAbs_COMPSOLID)
    topo_list["compsolid"] = compsolid_list

    #find all the solids
    solid_list = geom_explorer(occ_compound, TopAbs_SOLID)
    topo_list["solid"] = solid_list

    #find all the shells
    shell_list = geom_explorer(occ_compound, TopAbs_SHELL)
    topo_list["shell"] = shell_list

    #find all the faces
    face_list = geom_explorer(occ_compound, TopAbs_FACE)
    topo_list["face"] = face_list

    #find all the wires
    wire_list = geom_explorer(occ_compound, TopAbs_WIRE)
    topo_list["wire"] = wire_list

    #find all the edges
    edge_list = geom_explorer(occ_compound, TopAbs_EDGE)
    topo_list["edge"] = edge_list

    #find all the vertices
    vertex_list = geom_explorer(occ_compound, TopAbs_VERTEX)
    topo_list["vertex"] = vertex_list
    
    return topo_list
    
def is_compound_null(occ_compound):
    isnull = True
    
    #find all the compsolids
    compsolid_list = geom_explorer(occ_compound, TopAbs_COMPSOLID)
    if compsolid_list:
        isnull = False

    #find all the solids
    solid_list = geom_explorer(occ_compound, TopAbs_SOLID)
    if solid_list:
        isnull = False

    #find all the shells
    shell_list = geom_explorer(occ_compound, TopAbs_SHELL)
    if shell_list:
        isnull = False

    #find all the faces
    face_list = geom_explorer(occ_compound, TopAbs_FACE)
    if face_list:
        isnull = False

    #find all the wires
    wire_list = geom_explorer(occ_compound, TopAbs_WIRE)
    if wire_list:
        isnull =False

    #find all the edges
    edge_list = geom_explorer(occ_compound, TopAbs_EDGE)
    if edge_list:
        isnull= False

    #find all the vertices
    vertex_list = geom_explorer(occ_compound, TopAbs_VERTEX)
    if vertex_list:
        isnull = False
    
    return isnull
            
def solids_frm_compsolid(occ_compsolid):
    solid_list = Topology.Topo(occ_compsolid).solids()
    return list(solid_list)
    
def shells_frm_solid(occ_solid):
    shell_list = Topology.Topo(occ_solid).shells()
    return list(shell_list)

def faces_frm_shell(occ_shell):
    face_list = Topology.Topo(occ_shell).faces()
    return list(face_list)
    
def faces_frm_solid(occ_solid):
    face_list = []
    shell_list = shells_frm_solid(occ_solid)
    for shell in shell_list:
        faces = faces_frm_shell(shell)
        face_list.extend(faces)
    return face_list
    
def wires_frm_face(occ_face):
    wire_list =  Topology.Topo(occ_face).wires()
    return list(wire_list)

def edges_frm_wire(occ_wire):
    edge_list = Topology.WireExplorer(occ_wire).ordered_edges()
    return list(edge_list)
    
def points_frm_wire(occ_wire):
    '''
    vertex_list = geom_explorer(occ_wire, TopAbs_VERTEX)
    point_list = vertex_list_2_point_list(vertex_list)
    
    n_pt_list = []
    for pt in point_list:
        if n_pt_list:
            p_vert = (n_pt_list[-1].X(), n_pt_list[-1].Y(), n_pt_list[-1].Z())
            c_vert = (pt.X(), pt.Y(), pt.Z())
            if c_vert != p_vert:
                n_pt_list.append(pt)
        else:
            n_pt_list.append(pt)
    
    return n_pt_list
    '''
    #TODO: WHEN DEALING WITH OPEN WIRE IT WILL NOT RETURN THE LAST VERTEX
    verts = Topology.WireExplorer(occ_wire).ordered_vertices()
    point_list = []
    for vert in verts:
        pt = BRep_Tool.Pnt(vert)
        point_list.append(pt)

    #this always returns points in order that is opposite of the input
    #e.g. if the inputs are clockwise it will ouput anticlockwise
    #e.g. if the inputs are anticlockwise it will ouput clockwise
    #thus the point list needs to be reversed to reflect the true order
    #point_list = list(reversed(point_list))
    
    return point_list
    
def points_frm_solid(occ_solid):
    verts = Topology.Topo(occ_solid).vertices()
    point_list = []
    for vert in verts:
        pt = BRep_Tool.Pnt(vert)
        point_list.append(pt)
        
    return point_list

def points_from_edge(occ_edge):
    vertex_list = list(Topology.Topo(occ_edge).vertices())
    point_list = vertex_list_2_point_list(vertex_list)
    return point_list