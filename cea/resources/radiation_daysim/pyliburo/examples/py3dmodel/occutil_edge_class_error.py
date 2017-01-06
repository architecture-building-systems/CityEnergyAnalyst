from OCC.gp import gp_Pnt
from OCC.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakeEdge
from OCCUtils import edge


def make_edge(pypt1, pypt2):
    gp_point1 = gp_Pnt(pypt1[0], pypt1[1], pypt1[2])
    gp_point2 = gp_Pnt(pypt2[0], pypt2[1], pypt2[2])
        
    make_edge = BRepBuilderAPI_MakeEdge(gp_point1, gp_point2)
    return make_edge.Edge()
    
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
    
#point to be projected
orig_pnt = gp_Pnt(0, 0, 10)

#edge to be projected to
dest_edge = make_edge((50,100,0), (50,20,0))
occutil_edge = edge.Edge(dest_edge)

#project point to edge
u, projpt = occutil_edge.project_vertex(orig_pnt)

#face the edge will intersect with
inter_face = make_polygon(((30,75,0),(60,75,0),(60,75,50),(30,75,50)))
#intersect edge with face
interptlist = occutil_edge.Intersect.intersect(inter_face, 1e-2)