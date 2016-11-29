import math

from OCCUtils import face, Common, Construct, Topology
from OCC import BRepFeat 
from OCC.gp import gp_Pnt, gp_Vec
from OCC.TopAbs import TopAbs_IN, TopAbs_REVERSED
from OCC.BRepClass3d import BRepClass3d_SolidClassifier
from OCC.GProp import GProp_GProps
from OCC.BRepGProp import brepgprop_VolumeProperties
from OCC.BOPInt import BOPInt_Context
from OCC.BRepCheck import BRepCheck_Wire
from OCC.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCC.BRep import BRep_Tool

def get_bounding_box(occ_shape):
    return Common.get_boundingbox(occ_shape)
    
def point_in_solid(occ_solid, pypt):
    gp_pnt = gp_Pnt(pypt[0], pypt[1], pypt[2] )
    if Common.point_in_solid(occ_solid, gp_pnt)[0]:
        return True 
    elif Common.point_in_solid(occ_solid, gp_pnt)[0] == None:
        return None #means its on the solid
    else: 
        return False
        
def minimum_distance(occ_shape1, occ_shape2):
    min_dist, min_dist_shp1, min_dist_shp2 = Common.minimum_distance(occ_shape1, occ_shape2)
    return min_dist
    
def face_normal(occface):
    fc = face.Face(occface)
    centre_uv, centre_pt = fc.mid_point()
    normal_dir = fc.DiffGeom.normal(centre_uv[0], centre_uv[1])

    if occface.Orientation() == TopAbs_REVERSED:
        normal_dir = normal_dir.Reversed()


    normal = (normal_dir.X(), normal_dir.Y(), normal_dir.Z())

    return normal
    
def face_midpt(occface):
    fc = face.Face(occface)
    centre_uv,gpcentre_pt = fc.mid_point()
    centre_pt = (gpcentre_pt.X(), gpcentre_pt.Y(), gpcentre_pt.Z())
    return centre_pt
    
def is_anticlockwise(pyptlist, pyref_vec):
    total = [0,0,0]    
    npts = len(pyptlist)
    for i in range(npts):
        pt1 = pyptlist[i]
        if i == npts-1:
            pt2 = pyptlist[0]
        else:
            pt2 = pyptlist[i+1]
            
        #cross the two pts
        vec1 = gp_Vec(pt1[0],pt1[1],pt1[2])
        vec2 = gp_Vec(pt2[0],pt2[1],pt2[2])
        prod = vec1.Crossed(vec2)
        total[0] += prod.X()
        total[1] += prod.Y()
        total[2] += prod.Z()
        
    gp_total = gp_Vec(total[0],total[1],total[2])
    gp_ref_vec = gp_Vec(pyref_vec[0],pyref_vec[1],pyref_vec[2])
    result  = gp_total.Dot(gp_ref_vec)
    if result < 0:
        return False 
    else:
        return True
        
def face_area(occ_face):
    surface_area = Common.GpropsFromShape(occ_face).surface()
    return surface_area.Mass()
    
def solid_volume(occ_solid):
    props = GProp_GProps()
    brepgprop_VolumeProperties(occ_solid, props)
    volume = props.Mass()
    return volume
    
def face_is_inside(occ_face, occ_boundary_face):
    return BRepFeat.brepfeat_IsInside(occ_face, occ_boundary_face)

def point_in_face(pypt, occ_face, tol=0.0001):
    gp_pt = gp_Pnt(pypt[0], pypt[1], pypt[2])
    isinside = BOPInt_Context().IsValidPointForFace(gp_pt, occ_face,tol )
    return isinside
    
def check_solid_inward(occ_solid):
    classify = BRepClass3d_SolidClassifier()
    classify.Load(occ_solid)
    classify.PerformInfinitePoint(0.001)
    state = classify.State()
    if state == TopAbs_IN:
        return True 
    else:
        return False 
        
def check_wire_closed(occ_wire):
    wire_checker = BRepCheck_Wire(occ_wire)
    return wire_checker.Closed()
     
def project_edge_on_face(occface, occ_edge):
    fc = face.Face(occface)
    projected_curve = fc.project_curve(occ_edge)
    return projected_curve
    
def srf_nrml_facing_solid_inward(occ_face, occ_solid):
    #move the face in the direction of the normal
    #first offset the face so that vert will be within the solid 
    o_wire = Construct.make_offset(occ_face, 0.0001)
    o_face = BRepBuilderAPI_MakeFace(o_wire).Face()
    
    wire_list =  list(Topology.Topo(o_face).wires())
    occpt_list = []
    for wire in wire_list:
        occpts = Topology.WireExplorer(wire).ordered_vertices()
        occpt_list.extend(occpts)
        
        
    pt = BRep_Tool.Pnt(occpt_list[0]) #a point that is on the edge of the face 
    normal = face_normal(occ_face)
    
    gp_direction2move = gp_Vec(normal[0], normal[1], normal[2])
    gp_moved_pt = pt.Translated(gp_direction2move.Multiplied(0.001))
    mv_pt = (gp_moved_pt.X(), gp_moved_pt.Y(), gp_moved_pt.Z())
    
    in_solid = point_in_solid(occ_solid, mv_pt)
    
    if in_solid:
        return True
    else:
        return False
        
def angle_bw_2_vecs(occvec1, occvec2):
    radangle = occvec1.Angle(occvec2)
    angle = radangle * (180.0/math.pi)
    return angle
    
    