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
from OCCUtils import Topology,edge
from OCC.BRep import BRep_Tool
from OCC.TopExp import TopExp_Explorer
from OCC.TopAbs import TopAbs_COMPOUND, TopAbs_COMPSOLID, TopAbs_SOLID, TopAbs_SHELL, TopAbs_FACE, TopAbs_WIRE, TopAbs_EDGE, TopAbs_VERTEX, TopAbs_REVERSED
from OCC.TopoDS import topods_Compound, topods_CompSolid, topods_Solid, topods_Shell, topods_Face, topods_Wire, topods_Edge, topods_Vertex
from OCC.Geom import Handle_Geom_BSplineCurve
from OCC.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
from OCC.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_HCurve
import calculate
import construct

def pyptlist_frm_occface(occ_face):
    wire_list = wires_frm_face(occ_face)
    occpt_list = []
    pt_list = []
    for wire in wire_list:
        occpts = points_frm_wire(wire)
        occpt_list.extend(occpts)
        
    for occpt in occpt_list:
        pt = (occpt.X(), occpt.Y(), occpt.Z()) 
        pt_list.append(pt)
    
    normal = calculate.face_normal(occ_face)
    anticlockwise = calculate.is_anticlockwise(pt_list, normal)
    if anticlockwise:
        pt_list.reverse()
        return pt_list
    else:
        return pt_list
    
def pyptlist_frm_occwire(occ_wire):
    pt_list = []
    occpt_list = points_frm_wire(occ_wire)
    for occpt in occpt_list:
        pt = (occpt.X(), occpt.Y(), occpt.Z()) 
        pt_list.append(pt)
    return pt_list
    
def occpt2pypt(occpt):
    pypt = (occpt.X(), occpt.Y(), occpt.Z())
    return pypt

def occptlist2pyptlist(occptlist):
    pyptlist = []
    for occpt in occptlist:
        pypt = occpt2pypt(occpt)
        pyptlist.append(pypt)
    return pyptlist

def vertex2point(occ_vertex):
    occ_pnt = BRep_Tool.Pnt(occ_vertex)
    return occ_pnt

def vertex_list_2_point_list(occ_vertex_list):
    point_list = []
    for vert in occ_vertex_list:
        point_list.append(BRep_Tool.Pnt(vert))
    return point_list
    
def pyptlist2vertlist(pyptlist):
    vertlist = []
    for pypt in pyptlist:
        vert = construct.make_vertex(pypt)
        vertlist.append(vert)
    return vertlist
    
def get_shapetype(occ_shape):
    shapetype = occ_shape.ShapeType()
    return shapetype
    
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

def geom_explorer(geom2explore, shapetype2find):
    geom_list = []
    if shapetype2find == "compound":
        shapetype2find_topABS = TopAbs_COMPOUND
    if shapetype2find == "compsolid":
        shapetype2find_topABS = TopAbs_COMPSOLID
    if shapetype2find == "solid":
        shapetype2find_topABS = TopAbs_SOLID
    if shapetype2find == "shell":
        shapetype2find_topABS = TopAbs_SHELL
    if shapetype2find == "face":
        shapetype2find_topABS = TopAbs_FACE
    if shapetype2find == "wire":
        shapetype2find_topABS = TopAbs_WIRE
    if shapetype2find == "edge":
        shapetype2find_topABS = TopAbs_EDGE
    if shapetype2find == "vertex":
        shapetype2find_topABS = TopAbs_VERTEX
        
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
    compsolid_list = geom_explorer(occ_compound, "compsolid")
    topo_list["compsolid"] = compsolid_list

    #find all the solids
    solid_list = geom_explorer(occ_compound, "solid")
    topo_list["solid"] = solid_list

    #find all the shells
    shell_list = geom_explorer(occ_compound, "shell")
    topo_list["shell"] = shell_list

    #find all the faces
    face_list = geom_explorer(occ_compound, "face")
    topo_list["face"] = face_list

    #find all the wires
    wire_list = geom_explorer(occ_compound, "wire")
    topo_list["wire"] = wire_list

    #find all the edges
    edge_list = geom_explorer(occ_compound, "edge")
    topo_list["edge"] = edge_list

    #find all the vertices
    vertex_list = geom_explorer(occ_compound, "vertex")
    topo_list["vertex"] = vertex_list
    
    return topo_list
    
def is_compound_null(occ_compound):
    isnull = True
    
    #find all the compsolids
    compsolid_list = geom_explorer(occ_compound, "compsolid")
    if compsolid_list:
        isnull = False

    #find all the solids
    solid_list = geom_explorer(occ_compound, "solid")
    if solid_list:
        isnull = False

    #find all the shells
    shell_list = geom_explorer(occ_compound, "shell")
    if shell_list:
        isnull = False

    #find all the faces
    face_list = geom_explorer(occ_compound, "face")
    if face_list:
        isnull = False

    #find all the wires
    wire_list = geom_explorer(occ_compound, "wire")
    if wire_list:
        isnull =False

    #find all the edges
    edge_list = geom_explorer(occ_compound, "edge")
    if edge_list:
        isnull= False

    #find all the vertices
    vertex_list = geom_explorer(occ_compound, "vertex")
    if vertex_list:
        isnull = False
    
    return isnull
    
def is_face_null(occface):
    return occface.IsNull()
            
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
    
def is_edge_bspline(occedge):
    adaptor = BRepAdaptor_Curve(occedge)
    '''
    GeomAbs_Line 	        0
    GeomAbs_Circle 	        1
    GeomAbs_Ellipse         2	
    GeomAbs_Hyperbola       3 	
    GeomAbs_Parabola        4	
    GeomAbs_BezierCurve     5	
    GeomAbs_BSplineCurve    6	
    GeomAbs_OtherCurve      7
    '''
    ctype = adaptor.GetType()
    if ctype == 6:
        return True
    else:
        return False

def is_edge_line(occedge):
    adaptor = BRepAdaptor_Curve(occedge)
    '''
    GeomAbs_Line 	        0
    GeomAbs_Circle 	        1
    GeomAbs_Ellipse         2	
    GeomAbs_Hyperbola       3 	
    GeomAbs_Parabola        4	
    GeomAbs_BezierCurve     5	
    GeomAbs_BSplineCurve    6	
    GeomAbs_OtherCurve      7
    '''
    ctype = adaptor.GetType()
    if ctype == 0:
        return True
    else:
        return False

    
def poles_from_bsplinecurve_edge(occedge):
    '''
    occedge: the edge to be measured
    type: occedge
    '''
    #occutil_edge = edge.Edge(occedge)
    adaptor = BRepAdaptor_Curve(occedge)
    adaptor_handle = BRepAdaptor_HCurve(adaptor)
    handle_bspline = Handle_Geom_BSplineCurve()
    bspline = handle_bspline.DownCast(adaptor.Curve().Curve()).GetObject()

    npoles =  bspline.NbPoles()
    polelist = []
    for np in range(npoles):
        pole = bspline.Pole(np+1)
        pypole = (pole.X(), pole.Y(), pole.Z())
        polelist.append(pypole)
        
    if topods_Edge(occedge).Orientation() == TopAbs_REVERSED:
        polelist.reverse()

    return polelist

def edge_domain(occedge):
    occutil_edge = edge.Edge(occedge)
    lbound, ubound = occutil_edge.domain()
    return lbound, ubound