import math
import colorsys

import numpy as np
from scipy.spatial import Delaunay

from OCC.Display.SimpleGui import init_display
from OCCUtils import face, Construct, Topology
from OCC.Display import OCCViewer
from OCC.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakeEdge, BRepBuilderAPI_Sewing
from OCC.BRepPrimAPI import BRepPrimAPI_MakePrism, BRepPrimAPI_MakeBox
from OCC.gp import gp_Pnt, gp_Vec, gp_Circ, gp_Ax2, gp_Dir
from OCC.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCC.BRepAlgoAPI import BRepAlgoAPI_Common
from OCC.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
from OCC.TopTools import TopTools_HSequenceOfShape, Handle_TopTools_HSequenceOfShape

from . import fetch
from . import calculate

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
    
def make_edge(pypt1, pypt2):
    gp_point1 = gp_Pnt(pypt1[0], pypt1[1], pypt1[2])
    gp_point2 = gp_Pnt(pypt2[0], pypt2[1], pypt2[2])
        
    make_edge = BRepBuilderAPI_MakeEdge(gp_point1, gp_point2)
    return make_edge.Edge()
    
def make_wire(pyptlist):
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
    return circle_edge
    
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
    
def make_shell_frm_faces(occ_face_list, tolerance = 1e-06):
    #make shell
    sewing = BRepBuilderAPI_Sewing()
    sewing.SetTolerance(tolerance)
    for f in occ_face_list:
        sewing.Add(f)
        
    sewing.Perform()
    sewing_shape = fetch.shape2shapetype(sewing.SewedShape())
    topo_dict = fetch.topos_frm_compound(sewing_shape)
    shell = topo_dict["shell"][0]
    return shell
    
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

def wire_frm_loose_edges(occedge_list):
    edges = TopTools_HSequenceOfShape()
    edges_handle = Handle_TopTools_HSequenceOfShape(edges)
    
    wires = TopTools_HSequenceOfShape()
    wires_handle = Handle_TopTools_HSequenceOfShape(wires)
    
    # The edges are copied to the sequence
    for edge in occedge_list: edges.Append(edge)
                
    # A wire is formed by connecting the edges
    ShapeAnalysis_FreeBounds.ConnectEdgesToWires(edges_handle, 1e-5, True, wires_handle)
    wires = wires_handle.GetObject()
        
    # From each wire a face is created
    face_list = []
    for i in range(wires.Length()):
        wire_shape = wires.Value(i+1)
        wire = fetch.shape2shapetype(wire_shape)
        face = BRepBuilderAPI_MakeFace(wire).Face()
        face_list.append(face)
        
    return face_list
        
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
        
    display.set_bg_gradient_color(0, 0, 0, 0, 0, 0)
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
    
def visualise_falsecolour_topo(results, occtopo_list, falsecolour_file, image_file, 
                               other_topo2dlist = None, other_colourlist = None, minval_range = None, maxval_range = None):
                                   
    display, start_display, add_menu, add_function_to_menu = init_display(backend_str = "wx")
    
    if minval_range == None: 
        minval = min(results)
    elif minval_range != None:
        minval = minval_range
    
    if maxval_range == None: 
        maxval = max(results)
    elif maxval_range != None: 
        maxval = maxval_range
        
    res_colours = falsecolour(results, minval, maxval)
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
    display.ExportToImage(image_file)
    start_display()