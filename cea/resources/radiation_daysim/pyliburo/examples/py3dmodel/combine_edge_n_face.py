import pyliburo

points1 = [(50,100,0), (75,75,0), (75,60,0),(100,60,0),(100,50,0), (50,0,0),(0,50,0)]#clockwise
face1 = pyliburo.py3dmodel.construct.make_polygon(points1)
points2 = [(50,50,0), (25,100,0), (50,150,0), (75,100,0)]
face2 = pyliburo.py3dmodel.construct.make_polygon(points2)

#pypt1 = (0,0,0)
#pypt2 = (75,150,0) 
#pypt3 = (100,300,0)
test_pyptlist = [(0.0, 0.0, 0.0), (16.666666666666668, 33.33333333333333, 0.0), (16.66666666666667, 33.333333333333336, 0.0), (0.0, 50.00000000000001, 0.0), (50.00000000000001, 100.00000000000001, 0.0), (50.0, 100.0, 0.0), (75.0, 150.0, 0.0), (75.0, 150.0, 0.0), (100.0, 300.0, 0.0)]
inputedge = pyliburo.py3dmodel.construct.make_wire(test_pyptlist)

res = pyliburo.py3dmodel.fetch.shape2shapetype(pyliburo.py3dmodel.construct.boolean_common(face2,inputedge))
res2 =pyliburo.py3dmodel.fetch.shape2shapetype(pyliburo.py3dmodel.construct.boolean_difference(inputedge,face2))
edgelist = pyliburo.py3dmodel.fetch.geom_explorer(res, "edge")
edgelist2 = pyliburo.py3dmodel.fetch.geom_explorer(res2, "edge")

wire = pyliburo.py3dmodel.fetch.wires_frm_face(face2)[0]
#turn the wire into a degree1 bspline curve edge
pyptlist = pyliburo.py3dmodel.fetch.occptlist2pyptlist(pyliburo.py3dmodel.fetch.points_frm_wire(wire))
pyptlist.append(pyptlist[0])
bwire = pyliburo.py3dmodel.construct.make_wire(pyptlist)
bspline_edge  =  pyliburo.py3dmodel.construct.make_bspline_edge(pyptlist, mindegree=1, maxdegree=1)

interptlist = []
for edge in edgelist:
    interpts = pyliburo.py3dmodel.calculate.intersect_edge_with_edge(bspline_edge, edge)
    interptlist.extend(interpts)

interptlist = pyliburo.py3dmodel.modify.rmv_duplicated_pts(interptlist)
eparmlist = []

for interpt in interptlist:
    eparm = pyliburo.py3dmodel.calculate.pt2edgeparameter(interpt, bspline_edge)
    eparmlist.append(eparm)
    
eparmlist.sort()
edmin,edmax = pyliburo.py3dmodel.fetch.edge_domain(bspline_edge)
eparm_range1 = eparmlist[-1] - eparmlist[0]
eparm_range21 = eparmlist[0] - edmin
eparm_range22 = edmax-eparmlist[-1]
eparm_range2 = eparm_range21 + eparm_range22

if eparm_range1 < eparm_range2 or eparm_range1 == eparm_range2 :
    te = pyliburo.py3dmodel.modify.trimedge(eparmlist[0],eparmlist[-1], bspline_edge)
    telength = pyliburo.py3dmodel.calculate.edgelength(eparmlist[0],eparmlist[-1], bspline_edge)
    edgelist2.append(te)
    sorted_edge2dlist = pyliburo.py3dmodel.calculate.sort_edges_into_order(edgelist2)
    
if eparm_range1 > eparm_range2:
    te1 = pyliburo.py3dmodel.modify.trimedge(edmin, eparmlist[0], bspline_edge)
    te2 = pyliburo.py3dmodel.modify.trimedge(eparmlist[-1], edmax, bspline_edge)
    edgelist2.append(te1)
    edgelist2.append(te2)
    telength1 = pyliburo.py3dmodel.calculate.edgelength(edmin, eparmlist[0], bspline_edge)
    telength2 = pyliburo.py3dmodel.calculate.edgelength(eparmlist[-1],edmax, bspline_edge)
    telength = telength1+telength2
    sorted_edge2dlist = pyliburo.py3dmodel.calculate.sort_edges_into_order(edgelist2)
    
sorted_edgelist = sorted_edge2dlist[0]

#turn the wire into a degree1 bspline curve edge
new_pyptlist = []
for sorted_edge in sorted_edgelist:
    if pyliburo.py3dmodel.fetch.is_edge_bspline(sorted_edge):
        pts = pyliburo.py3dmodel.fetch.poles_from_bsplinecurve_edge(sorted_edge)
    if pyliburo.py3dmodel.fetch.is_edge_line(sorted_edge):
        pts = pyliburo.py3dmodel.fetch.occptlist2pyptlist(pyliburo.py3dmodel.fetch.points_from_edge(sorted_edge))
        
    new_pyptlist.extend(pts)
    
new_bwire = pyliburo.py3dmodel.construct.make_wire(new_pyptlist)    
wirelength = pyliburo.py3dmodel.calculate.wirelength(new_bwire)
print wirelength
display2dlist = []
display2dlist.append([wire])
display2dlist.append([new_bwire])
pyliburo.py3dmodel.construct.visualise(display2dlist, ["WHITE", "RED"])
