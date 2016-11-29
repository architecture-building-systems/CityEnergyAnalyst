from OCCUtils import Construct
from OCC.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.gp import gp_Pnt, gp_Vec, gp_Ax1, gp_Ax3, gp_Dir, gp_DZ, gp_Trsf
from OCC.ShapeFix import ShapeFix_Shell
from OCC.BRepLib import breplib

from . import fetch

def move(orig_pt, location_pt, shape):
    gp_ax31 = gp_Ax3(gp_Pnt(orig_pt[0], orig_pt[1], orig_pt[2]), gp_DZ())
    gp_ax32 = gp_Ax3(gp_Pnt(location_pt[0], location_pt[1], location_pt[2]), gp_DZ())
    aTrsf = gp_Trsf()
    aTrsf.SetTransformation(gp_ax32,gp_ax31)
    trsf_shp = BRepBuilderAPI_Transform(shape, aTrsf).Shape()
    return trsf_shp
    
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