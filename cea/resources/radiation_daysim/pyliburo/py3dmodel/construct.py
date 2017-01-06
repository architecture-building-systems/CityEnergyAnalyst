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
import math
import colorsys

import numpy as np
from scipy.spatial import Delaunay

from OCC.Display.SimpleGui import init_display
from OCCUtils import face, Construct, Topology, Common
from OCC.Display import OCCViewer
from OCC.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakeEdge, BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid, BRepBuilderAPI_MakeWire
from OCC.BRepPrimAPI import BRepPrimAPI_MakePrism, BRepPrimAPI_MakeBox
from OCC.gp import gp_Pnt, gp_Vec, gp_Lin, gp_Circ, gp_Ax1, gp_Ax2, gp_Dir
from OCC.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCC.BRepAlgoAPI import BRepAlgoAPI_Common
from OCC.TopTools import TopTools_HSequenceOfShape, Handle_TopTools_HSequenceOfShape
from OCC.GeomAPI import GeomAPI_PointsToBSpline
from OCC.TColgp import TColgp_Array1OfPnt
from OCC.BRep import BRep_Builder
from OCC.TopoDS import TopoDS_Shell

import fetch
import calculate
import modify

def make_polygon(pyptlist):   
    array = []
    for pt in pyptlist:
        array.append(gp_Pnt(pt[0],pt[1],pt[2]))

    poly = BRepBuilderAPI_MakePolygon()
    map(poly.Add, array)
    poly.Build()
    poly.Close()
    
    wire = poly.Wire()
    occface = BRepBuilderAPI_MakeFace(wire)
    return occface.Face()
    
def make_vertex(pypt):
    gppt = make_gppnt(pypt)
    vert = Construct.make_vertex(gppt)
    return vert

def make_plane_w_dir(centre_pypt, normal_pydir):
    plane_face = Construct.make_plane(center=gp_Pnt(centre_pypt[0],centre_pypt[1],centre_pypt[2]), 
                         vec_normal = gp_Vec(normal_pydir[0], normal_pydir[1], normal_pydir[2]))
    return plane_face
    
def make_edge(pypt1, pypt2):
    gp_point1 = gp_Pnt(pypt1[0], pypt1[1], pypt1[2])
    gp_point2 = gp_Pnt(pypt2[0], pypt2[1], pypt2[2])
        
    make_edge = BRepBuilderAPI_MakeEdge(gp_point1, gp_point2)
    return make_edge.Edge()
    
def make_bspline_edge(pyptlist, mindegree=3, maxdegree = 8):
    array = TColgp_Array1OfPnt(1, len(pyptlist))
    pcnt = 1
    for pypt in pyptlist:
        gppt = make_gppnt(pypt)
        array.SetValue(pcnt, gppt)
        pcnt+=1
    bcurve =GeomAPI_PointsToBSpline(array,mindegree,maxdegree).Curve()
    curve_edge = BRepBuilderAPI_MakeEdge(bcurve)
    return curve_edge.Edge()
    
def make_bspline_edge_interpolate(pyptlist, is_closed):
    '''
    pyptlist: list of pypt
    type: list(tuple)
    
    is_closed: is the curve open or close
    type: bool, True or False
    '''
    gpptlist = make_gppntlist(pyptlist)
    bcurve = Common.interpolate_points_to_spline_no_tangency(gpptlist, closed=is_closed)
    curve_edge = BRepBuilderAPI_MakeEdge(bcurve)
    return curve_edge.Edge()
    
def make_wire(pyptlist):
    '''
    if you want a close wire, make sure the pts the first pts too
    '''
    array = []
    for pt in pyptlist:
        array.append(gp_Pnt(pt[0],pt[1],pt[2]))

    poly = BRepBuilderAPI_MakePolygon()
    map(poly.Add, array)
    poly.Build()
    wire = poly.Wire()
    return wire
    
def make_wire_frm_edges(occ_edge_list):
    wire = Construct.make_wire(occ_edge_list)
    return wire
    
def make_loft_with_wires(occ_wire_list):
    loft = Construct.make_loft(occ_wire_list, ruled = False)
    return loft
    
def make_loft(occ_face_list, rule_face = True):
    #get the wires from the face_list
    wire_list = []
    for f in occ_face_list:
        wires = fetch.wires_frm_face(f)
        wire_list.extend(wires)
        
    loft = Construct.make_loft(wire_list, ruled = rule_face)
    return loft
    
def make_rectangle(xdim, ydim):
    point_list = [((xdim/2.0)*-1, ydim/2.0, 0), (xdim/2.0, ydim/2.0, 0), (xdim/2.0, (ydim/2.0)*-1, 0), ((xdim/2.0)*-1, (ydim/2.0)*-1, 0)]
    face = make_polygon(point_list)
    return face
    
def make_circle(pycentre_pt, pydirection, radius):
    circle = gp_Circ(gp_Ax2(gp_Pnt(pycentre_pt[0], pycentre_pt[1], pycentre_pt[2]), gp_Dir(pydirection[0], pydirection[1], pydirection[2])), radius)
    circle_edge = BRepBuilderAPI_MakeEdge(circle, 0, circle.Length())
    return circle_edge.Edge()
    
def circles_frm_pyptlist(pyptlist, radius):
    circlelist = []
    gpptlist = make_gppntlist(pyptlist)
    for gppt in gpptlist:
        circle = make_circle((gppt.X(),gppt.Y(),gppt.Z()), (0,0,1), radius)
        circlelist.append(circle)
    return circlelist
            
def make_box(length, width, height):
    box = fetch.shape2shapetype(BRepPrimAPI_MakeBox(length,width,height).Shape())
    return box
    
def make_offset(occ_face, offset_value):
    o_wire = Construct.make_offset(occ_face, offset_value)
    occface = BRepBuilderAPI_MakeFace(o_wire)
    return occface.Face()
    
def make_offset_face2wire(occ_face, offset_value):
    o_wire = Construct.make_offset(occ_face, offset_value)
    return fetch.shape2shapetype(o_wire)
    
def make_vector(pypt1,pypt2):
    gp_pt1 = gp_Pnt(pypt1[0],pypt1[1],pypt1[2])
    gp_pt2 = gp_Pnt(pypt2[0],pypt2[1],pypt2[2])
    gp_vec = gp_Vec(gp_pt1, gp_pt2)
    return gp_vec
    
def make_gppnt(pypt):
    return gp_Pnt(pypt[0], pypt[1], pypt[2])
    
def make_gppntlist(pyptlist):
    gpptlist = []
    for pypt in pyptlist:
        gpptlist.append(make_gppnt(pypt))
    return gpptlist
    
def make_line(pypt, pydir):
    occ_line = gp_Lin(gp_Ax1(gp_Pnt(pypt[0], pypt[1], pypt[2]), gp_Dir(pydir[0], pydir[1], pydir[2])))
    return occ_line
    
def make_shell(occfacelist):
    builder = BRep_Builder()
    shell = TopoDS_Shell()
    builder.MakeShell(shell)
    for occface in occfacelist:
        builder.Add(shell, occface)
        
    return shell
    
def make_shell_frm_faces(occ_face_list, tolerance = 1e-06):
    #make shell
    sewing = BRepBuilderAPI_Sewing()
    sewing.SetTolerance(tolerance)
    for f in occ_face_list:
        sewing.Add(f)
        
    sewing.Perform()
    sewing_shape = fetch.shape2shapetype(sewing.SewedShape())
    topo_dict = fetch.topos_frm_compound(sewing_shape)
    shell_list = topo_dict["shell"]
    return shell_list
    
def make_solid(occ_shell):
    ms = BRepBuilderAPI_MakeSolid()
    ms.Add(occ_shell)
    return ms.Solid()
    
def make_solid_from_shell_list(occ_shell_list):
    ms = BRepBuilderAPI_MakeSolid()
    for occ_shell in occ_shell_list:
        ms.Add(occ_shell)
    return ms.Solid()
    
def make_compound(topo):
    return Construct.compound(topo)
    
def extrude(occ_face, pyvector, height):
    vec = make_vector((0,0,0),pyvector)*height
    extrude = BRepPrimAPI_MakePrism(occ_face, vec)
    return extrude.Shape()
    
def extrude_edge(occedge, pydirection, height):
    edge_midpt = calculate.edge_midpt(occedge)
    location_pt = modify.move_pt(edge_midpt, pydirection, height)
    edge2 = fetch.shape2shapetype(modify.move(edge_midpt, location_pt, occedge))
    edge_wire = make_wire_frm_edges([occedge])
    edge_wire2 = make_wire_frm_edges([edge2])
    edgeface = make_loft_with_wires([edge_wire,edge_wire2])
    facelist = fetch.geom_explorer(edgeface, "face")
    return facelist[0]
    
def grid_face(occ_face, udim, vdim):
    #returns a series of polygons 
    pt_list = []
    face_list = []
    fc = face.Face(occ_face)
    umin, umax, vmin, vmax = fc.domain()
    u_div = int(math.ceil((umax-umin)/udim))
    v_div = int(math.ceil((vmax-vmin)/vdim))
    for ucnt in range(u_div+1):
        for vcnt in range(v_div+1):
            u = umin + (ucnt*udim)
            v = vmin + (vcnt*vdim)
            occpt = fc.parameter_to_point(u,v)
            pt = [occpt.X(),occpt.Y(),occpt.Z()]
            pt_list.append(pt)

    for pucnt in range(u_div):
        for pvcnt in range(v_div):
            pcnt = pucnt*(v_div+1) + pvcnt
            #print pcnt
            pt1 = pt_list[pcnt]
            pt2 = pt_list[pcnt+v_div+1]
            pt3 = pt_list[pcnt+v_div+2]
            pt4 = pt_list[pcnt+1]
            occface = make_polygon([pt1, pt2, pt3, pt4])
            face_list.append(occface)
            
    #intersect the grids and the face so that those grids that are not in the face will be erase
    intersection_list = []
    for f in face_list:
        intersection = BRepAlgoAPI_Common(f, occ_face).Shape()
        compound = fetch.shape2shapetype(intersection)
        inter_face_list = fetch.topos_frm_compound(compound)["face"]
        if inter_face_list:
            for inter_face in inter_face_list:
                intersection_list.append(inter_face)
    #return face_list
    return intersection_list

def boolean_common(occ_shape1, occ_shape2):
    intersection = BRepAlgoAPI_Common(occ_shape1, occ_shape2).Shape()
    return intersection
    
def boolean_fuse(occshape1, occshape2):
    fused = Construct.boolean_fuse(occshape1, occshape2)
    return fused

def boolean_difference(occshape2cutfrm, occ_cuttingshape):
    difference = Construct.boolean_cut(occshape2cutfrm, occ_cuttingshape)
    return difference
    
def make_face_frm_wire(occwire):
    occface = BRepBuilderAPI_MakeFace(occwire).Face()
    if not occface.IsNull():    
        return occface

def wire_frm_loose_edges(occedge_list):
    '''
    the edges need to be able to form a close face. IT does not work with a group of open edges
    need to change name to face from loose edges
    '''
    edges = TopTools_HSequenceOfShape()
    edges_handle = Handle_TopTools_HSequenceOfShape(edges)
    
    wires = TopTools_HSequenceOfShape()
    wires_handle = Handle_TopTools_HSequenceOfShape(wires)
    
    # The edges are copied to the sequence
    for edge in occedge_list: edges.Append(edge)
                
    # A wire is formed by connecting the edges
    ShapeAnalysis_FreeBounds.ConnectEdgesToWires(edges_handle, 1e-20, True, wires_handle)
    wires = wires_handle.GetObject()
        
    # From each wire a face is created
    face_list = []
    for i in range(wires.Length()):
        wire_shape = wires.Value(i+1)
        wire = fetch.shape2shapetype(wire_shape)
        face = BRepBuilderAPI_MakeFace(wire).Face()
        if not face.IsNull():
            face_list.append(face)
        
    return face_list
    
def arrange_edges_2_wires(occedgelist, isclosed = False):
    from OCC.TopoDS import topods 
    from OCC.TopExp import topexp
    from OCC.BRep import BRep_Tool
    from OCC.ShapeAnalysis import ShapeAnalysis_WireOrder
    from OCC.Precision import precision
    from OCC.BRepBuilderAPI import BRepBuilderAPI_WireDone, BRepBuilderAPI_EmptyWire, BRepBuilderAPI_DisconnectedWire, BRepBuilderAPI_NonManifoldWire
    
    wb_errdict={BRepBuilderAPI_WireDone:"No error", BRepBuilderAPI_EmptyWire:"Empty wire", BRepBuilderAPI_DisconnectedWire:"disconnected wire",
    BRepBuilderAPI_NonManifoldWire:"non-manifold wire"}
    
    sawo_statusdict={0:"all edges are direct and in sequence",
    1:"all edges are direct but some are not in sequence",
    2:"unresolved gaps remain",
    -1:"some edges are reversed, but no gaps remain",
    -2:"some edges are reversed and some gaps remain",
    -10:"failure on reorder"}
    
    mode3d = True
    SAWO = ShapeAnalysis_WireOrder(mode3d, precision.PConfusion())
    
    for edge in occedgelist:
        V1 = topexp.FirstVertex(topods.Edge(edge))
        V2 = topexp.LastVertex(topods.Edge(edge))
        pnt1 = BRep_Tool().Pnt(V1)
        pnt2 = BRep_Tool().Pnt(V2)
        SAWO.Add(pnt1.XYZ(), pnt2.XYZ())
        SAWO.SetKeepLoopsMode(True)
        
    SAWO.Perform(isclosed)
    #print "SAWO.Status()", SAWO.Status()
    if not SAWO.IsDone():
        raise RuntimeError, "build wire: Unable to reorder edges: \n" + sawo_statusdict[SAWO.Status()]
    else:
        if SAWO.Status() not in [0, -1]:
            pass # not critical, wirebuilder will handle this
        SAWO.SetChains(precision.PConfusion())
        wirelist = []
        #print "Number of chains: ", SAWO.NbChains()
        
        for i in range(SAWO.NbChains()):
            wirebuilder = BRepBuilderAPI_MakeWire()
            estart, eend = SAWO.Chain(i+1)
            #print "Number of edges in chain", i, ": ", eend - estart + 1
            if (eend - estart + 1)==0:
                continue
            for j in range(estart, eend+1):
                idx = abs(SAWO.Ordered(j)) # wirebuilder = s_addToWireBuilder(wirebuilder, edgelist[idx-1])
                edge2w = occedgelist[idx-1]
                wirebuilder.Add(edge2w)
                if wirebuilder is None:
                    raise RuntimeError, " build wire: Error adding edge number " + str(j+1) + " to Wire number " + str(i)
                    err = wirebuilder.Error()
                    if err != BRepBuilderAPI_WireDone:
                        raise RuntimeError, "Overlay2D: build wire: Error adding edge number " + str(j+1) + " to Wire number " + str(i) +": \n" + wb_errdict[err]
                        try:
                            wirebuilder.Build()
                            aWire = wirebuilder.Wire()
                            wirelist.append(aWire)
                        except Exception, err:
                            raise RuntimeError, "Overlay2D: build wire: Creation of Wire number " + str(i) + " from edge(s) failed. \n" + str(err)
        
            wirebuilder.Build()
            aWire = wirebuilder.Wire()
            wirelist.append(aWire)
            
    return wirelist
        
def merge_faces(occ_face_list, tolerance = 1e-06 ):
    sew = BRepBuilderAPI_Sewing(tolerance)
    for shp in occ_face_list:
        if isinstance(shp, list):
            for i in shp:
                sew.Add(i)
        else:
            sew.Add(shp)
            
    sew.Perform()
    nfreeedge = sew.NbFreeEdges()
    free_edges = []
    for fe_cnt in range(nfreeedge):
        free_edges.append(sew.FreeEdge(fe_cnt+1))
    face_list = wire_frm_loose_edges(free_edges)
    return face_list
    
def delaunay3d(pyptlist):
    pyptlistx = []
    pyptlisty = []
    pyptlistz = []
    
    for pypt in pyptlist:
        pyptlistx.append(pypt[0])
        pyptlisty.append(pypt[1])
        pyptlistz.append(pypt[2])
        
    # u, v are parameterisation variables
    u = np.array(pyptlistx) 
    v = np.array(pyptlisty) 
    
    x = u
    y = v
    z = np.array(pyptlistz)
    
    # Triangulate parameter space to determine the triangles
    tri = Delaunay(np.array([u,v]).T)
    
    occtriangles = []
    xyz = np.array([x,y,z]).T
    for verts in tri.simplices:
        pt1 = list(xyz[verts[0]])
        pt2 = list(xyz[verts[1]])
        pt3 = list(xyz[verts[2]])
        occtriangle = make_polygon([pt1,pt2,pt3])
        occtriangles.append(occtriangle)
    
    return occtriangles
    
def visualise(shape2dlist, colour_list):
    display, start_display, add_menu, add_function_to_menu = init_display()#init_display(backend_str = "wx")
    sc_cnt = 0
    for shape_list in shape2dlist:
        compound = make_compound(shape_list)
        colour = colour_list[sc_cnt]
        display.DisplayColoredShape(compound, color = colour, update=True)
        sc_cnt+=1
        
    display.set_bg_gradient_color(250, 250, 250, 250, 250, 250)
    display.View_Iso()
    display.FitAll()
    start_display()
    
def pseudocolor(val, minval, maxval):
    # convert val in range minval..maxval to the range 0..120 degrees which
    # correspond to the colors red..green in the HSV colorspace
    if val <= minval:
        h = 250.0
    elif val>=maxval:
        h = 0.0
    else:
        h = 250 - (((float(val-minval)) / (float(maxval-minval)))*250)
    # convert hsv color (h,1,1) to its rgb equivalent
    # note: the hsv_to_rgb() function expects h to be in the range 0..1 not 0..360
    r, g, b = colorsys.hsv_to_rgb(h/360, 1., 1.)
    return r, g, b
    
def falsecolour(results, minval, maxval):
    res_colours = []
    for result in results:
        r,g,b = pseudocolor(result, minval, maxval)
        colour = OCCViewer.color(r, g, b)
        res_colours.append(colour)
    return res_colours
    
def frange(start, stop, n):
    L = [0.0] * n
    nm1 = n - 1
    nm1inv = 1.0 / nm1
    for i in range(n):
        L[i] = nm1inv * (start*(nm1 - i) + stop*i)
    return L
    
def generate_falsecolour_bar(minval, maxval, export_path, display):
    xdim = 1
    ydim = 10
    rectangle = make_rectangle(xdim, ydim)
    grid_srfs = grid_face(rectangle, xdim, 1)
    #generate uniform results between max and min
    uni_res = frange(minval, maxval, 10)
    bar_colour = falsecolour(uni_res, minval, maxval)
    
    for scnt in range(len(grid_srfs)):
        srf = grid_srfs[scnt]
        fcolour = bar_colour[scnt]
        res = round(uni_res[scnt],2)
        txt_pt = make_gppnt(calculate.face_midpt(srf))
        display.DisplayColoredShape(srf, color=fcolour, update=True)
        if scnt == len(grid_srfs)-1:
            display.DisplayMessage(txt_pt, str(res) + "\nkWh/m2", height=None, message_color=(0,0,0), update=True)
        else:
            display.DisplayMessage(txt_pt, str(res), height=None, message_color=(0,0,0), update=True)
    
    display.set_bg_gradient_color(255, 255, 255, 255, 255, 255)
    display.View_Iso()
    display.FitAll()
    display.ExportToImage(export_path)
    display.EraseAll()
    
def visualise_falsecolour_topo(results, occtopo_list, falsecolour_file=None, image_file=None, 
                               other_topo2dlist = None, other_colourlist = None, minval_range = None, maxval_range = None):
                                   
    display, start_display, add_menu, add_function_to_menu = init_display()
    
    if minval_range == None: 
        minval = min(results)
    elif minval_range != None:
        minval = minval_range
    
    if maxval_range == None: 
        maxval = max(results)
    elif maxval_range != None: 
        maxval = maxval_range
        
    res_colours = falsecolour(results, minval, maxval)
    if falsecolour_file!=None:
        falsecolour_bar = generate_falsecolour_bar(minval, maxval, falsecolour_file, display)
    colour_list = []
    c_srf_list = []
    for r_cnt in range(len(res_colours)):
        fcolour = res_colours[r_cnt]
        rf = occtopo_list[r_cnt]
        if fcolour not in colour_list:
            colour_list.append(fcolour)
            c_srf_list.append([rf])
            
        elif fcolour in colour_list:
            c_index = colour_list.index(fcolour)
            c_srf_list[c_index].append(rf)
        
    for c_cnt in range(len(c_srf_list)):
        c_srfs = c_srf_list[c_cnt]
        colour = colour_list[c_cnt]
        compound = make_compound(c_srfs)
        display.DisplayColoredShape(compound, color=colour, update=True)
        
    #display the edges of the grid
    tedges = []
    for t in occtopo_list:
        edge = list(Topology.Topo(t).edges())
        tedges.extend(edge)
        
    edgecompound = make_compound(tedges)
    display.DisplayColoredShape(edgecompound, color="BLACK", update=True)
            
    if other_topo2dlist != None:
        tc_cnt = 0
        for other_topolist in other_topo2dlist:
            other_compound = make_compound(other_topolist)
            other_colour = other_colourlist[tc_cnt]
            display.DisplayColoredShape(other_compound, color=other_colour, update=True)
            tc_cnt +=1
    
    display.set_bg_gradient_color(0, 0, 0, 0, 0, 0)
    display.View_Iso()
    display.FitAll()
    if image_file !=None:
        display.ExportToImage(image_file)
    start_display()