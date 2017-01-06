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
from OCCUtils import Construct
from OCC.BRepBuilderAPI import BRepBuilderAPI_Transform, BRepBuilderAPI_MakeEdge, BRepBuilderAPI_GTransform
from OCC.gp import gp_Pnt, gp_Vec, gp_Ax1, gp_Ax3, gp_Dir, gp_DZ, gp_Trsf, gp_GTrsf, gp_Mat
from OCC.ShapeFix import ShapeFix_Shell
from OCC.BRepLib import breplib
from OCC.Geom import Geom_TrimmedCurve
from OCC.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_CompCurve, BRepAdaptor_HCompCurve
from OCC.GeomConvert import geomconvert_CurveToBSplineCurve

import fetch
import calculate

def move(orig_pt, location_pt, shape):
    gp_ax31 = gp_Ax3(gp_Pnt(orig_pt[0], orig_pt[1], orig_pt[2]), gp_DZ())
    gp_ax32 = gp_Ax3(gp_Pnt(location_pt[0], location_pt[1], location_pt[2]), gp_DZ())
    aTrsf = gp_Trsf()
    aTrsf.SetTransformation(gp_ax32,gp_ax31)
    trsf_shp = BRepBuilderAPI_Transform(shape, aTrsf).Shape()
    return trsf_shp
    
def normalise_vec(gpvec):
    ngpvec = gpvec.Normalized()
    return (ngpvec.X(), ngpvec.Y(), ngpvec.Z())
    
def rotate(shape, rot_pt, axis, degree):
    gp_ax3 = gp_Ax1(gp_Pnt(rot_pt[0], rot_pt[1], rot_pt[2]), gp_Dir(axis[0], axis[1], axis[2]))
    rot_shape = Construct.rotate(shape, gp_ax3, degree, copy=False)
    return rot_shape
    
def move_pt(orig_pt, direction2move, magnitude):
    gp_orig_pt = gp_Pnt(orig_pt[0], orig_pt[1],orig_pt[2])
    gp_direction2move = gp_Vec(direction2move[0], direction2move[1], direction2move[2])
    gp_moved_pt = gp_orig_pt.Translated(gp_direction2move.Multiplied(magnitude))
    moved_pt = (gp_moved_pt.X(), gp_moved_pt.Y(), gp_moved_pt.Z())
    return moved_pt
    
def uniform_scale(occshape, tx, ty, tz, ref_pypt):
    moved_shape = move(ref_pypt, (0,0,0),occshape)
    xform = gp_GTrsf()
    xform.SetVectorialPart(gp_Mat(
      tx, 0, 0,
      0, ty, 0,
      0, 0, tz,
    ))
    brep = BRepBuilderAPI_GTransform(moved_shape, xform, False)
    brep.Build()
    trsfshape = brep.Shape()
    move_back_shp = move((0,0,0), ref_pypt,trsfshape)
    return move_back_shp

def reverse_vector(vec):
    gp_rev_vec = gp_Vec(vec[0], vec[1], vec[2]).Reversed()
    rev_vec = (gp_rev_vec.X(), gp_rev_vec.Y(), gp_rev_vec.Z())
    return rev_vec
    
def reverse_face(occ_face):
    #reverse the face
    occ_face_r = fetch.shape2shapetype(occ_face.Reversed())
    return occ_face_r
    
def fix_shell_orientation(occ_shell):
    shapefix = ShapeFix_Shell()
    shapefix.FixFaceOrientation(occ_shell)
    shapefix.Perform()
    fix_shell = shapefix.Shell()
    return fix_shell
    
def fix_close_solid(occ_solid):
    breplib.OrientClosedSolid(occ_solid)
    return occ_solid
    
def fix_shape(occ_shape):
    fixed_shape = Construct.fix_shape(occ_shape)
    return fixed_shape
    
def fix_face(occ_face):
    fixed_face = Construct.fix_face(occ_face)
    return fixed_face
    
def rmv_duplicated_faces(occfacelist):
    fcnt = 0
    same_face_list = []
    non_dup_faces = []
    for occface in occfacelist:
        same_index = [fcnt]
        for fcnt2 in range(len(occfacelist)):
            if fcnt2 != fcnt:
                is_same = calculate.are_same_faces(occface, occfacelist[fcnt2])
                if is_same:
                    print is_same
                    same_index.append(fcnt2)
                    
        same_index.sort()
        if same_index not in same_face_list:
            same_face_list.append(same_index)                       
        fcnt +=1
        
    for indexes in same_face_list:
        unique_f = occfacelist[indexes[0]]
        non_dup_faces.append(unique_f)
    return non_dup_faces
    
def rmv_duplicated_edges(occedgelist):
    fcnt = 0
    same_edge_list = []
    non_dup_edges = []
    for occedge in occedgelist:
        same_index = [fcnt]
        for fcnt2 in range(len(occedgelist)):
            if fcnt2 != fcnt:
                is_same = calculate.are_same_edges(occedge, occedgelist[fcnt2])
                if is_same:
                    same_index.append(fcnt2)

        same_index.sort()
        if same_index not in same_edge_list:
            same_edge_list.append(same_index)                        
        fcnt +=1
        
    for indexes in same_edge_list:
        unique_f = occedgelist[indexes[0]]
        non_dup_edges.append(unique_f)
    return non_dup_edges
    
def rmv_duplicated_pts_by_distance(pyptlist, tolerance = 1e-06):
    '''
    fuse all pts in the list within a certain tolerance
    '''
    npyptlist = len(pyptlist)
    total_ptlist = []
    for ptcnt in range(npyptlist):
        ptlist = []
        ptlist.append(ptcnt)
        for ptcnt2 in range(npyptlist):
            if ptcnt != ptcnt2:
                ptdist = calculate.distance_between_2_pts(pyptlist[ptcnt], pyptlist[ptcnt2])
                if ptdist <= tolerance:
                    ptlist.append(ptcnt2)
                    
        ptlist.sort()
        if ptlist not in total_ptlist:
            total_ptlist.append(ptlist)
            
    upyptlist = []
    for upt in total_ptlist:
        upyptlist.append(pyptlist[upt[0]])
    return upyptlist
    
def rmv_duplicated_pts(pyptlist, roundndigit = None):
    '''
    fuse all pts in the list within a certain tolerance
    '''
    
    if roundndigit == None:
        upyptlist = set(pyptlist)
        return list(upyptlist)
        
    else:
        upyptlist = set(pyptlist)
        round_pyptlist = []
        for pypt in upyptlist:
            round_pypt = (round(pypt[0],roundndigit), round(pypt[1],roundndigit), round(pypt[2],roundndigit))
            if round_pypt not in round_pyptlist:
                round_pyptlist.append(round_pypt)
            
    return round_pyptlist
   
def round_pypt(pypt, roundndigit):
    rounded_pypt = (round(pypt[0],roundndigit), round(pypt[1],roundndigit), round(pypt[2],roundndigit))
    return rounded_pypt
    
def round_pyptlist(pyptlist, roundndigit):
    rounded_pyptlist = []
    for pypt in pyptlist:
        rounded_pypt = round_pypt(pypt, roundndigit)
        rounded_pyptlist.append(rounded_pypt)
    return rounded_pyptlist
    
def trimedge(lbound, ubound, occedge):
    '''
    lbound: lower bound of the parameterise edge
    type: float
    
    ubound: upper bound of the parameterise edge
    type: float
    
    occedge: the edge to be trimmed
    type: occedge
    '''
    adaptor = BRepAdaptor_Curve(occedge)
    #print adaptor.Trim(adaptor.FirstParameter(), adaptor.LastParameter(), adaptor.Tolerance()).GetObject().NbPoles().Curve()
    tr = Geom_TrimmedCurve(adaptor.Curve().Curve(), lbound, ubound)
    tr.SetTrim(lbound, ubound)
    bspline_handle = geomconvert_CurveToBSplineCurve(tr.GetHandle())
    #print tr.GetHandle()
    tr_edge = BRepBuilderAPI_MakeEdge(bspline_handle)
    #occutil_edge = edge.Edge(occedge)
    #trimedge = occutil_edge.trim(lbound, ubound)
    
    return tr_edge.Edge()
    
def trim_wire(occ_wire, shapeLimit1, shapeLimit2, is_periodic=False):
    '''
    occwire: wire to be trimmed
    type: occwire
    
    shapeLimit1: the 1st point where to cut the wire
    type: tuple, e.g. (0,1,2.5)
    
    shapeLimit1: the 2nd point where to cut the wire
    type: tuple, e.g. (0,1,2.5)
    
    is_periodic: indicate if the wire is open or close, true for close, false for open
    type: bool, e.g. True or False
    '''
    
    trimmed = Construct.trim_wire(occ_wire, shapeLimit1, shapeLimit2, periodic= is_periodic )
    return trimmed
    
def wire_2_bsplinecurve_edge(occwire):
    '''
    occwire: wire to be converted
    type: occwire
    '''
    adaptor = BRepAdaptor_CompCurve(occwire)
    hadap = BRepAdaptor_HCompCurve(adaptor)
    from OCC.Approx import Approx_Curve3d
    from OCC.GeomAbs import GeomAbs_C0, GeomAbs_C0, GeomAbs_C2, GeomAbs_C3
    approx = Approx_Curve3d(hadap.GetHandle(), 1e-06, GeomAbs_C2 , 10000, 12)
    bspline_handle = approx.Curve()
    occedge = BRepBuilderAPI_MakeEdge(bspline_handle)
    return occedge.Edge()