import pyliburo

displaylist1 = []
displaylist2 = []
displaylist3 = []
#point for projection
pypt = (0,0,10)

#face for projection
pyptlist = [(50,100,0), (60,80,0), (60,80,50),(50,100,60)]#clockwise
occ_face = pyliburo.py3dmodel.construct.make_polygon(pyptlist)
face_plane = pyliburo.py3dmodel.construct.make_plane_w_dir((5,5,3), (0,1,0))

pyptlist2 = [(30,30,0), (20,30,0), (20,40,0),(30,40,0)]#clockwise
face2project = pyliburo.py3dmodel.construct.make_polygon(pyptlist2)
projected_facepts = pyliburo.py3dmodel.calculate.project_face_on_faceplane(face_plane, face2project)
face_circles = []
print len(projected_facepts)
for facept in projected_facepts:    
    pyfacept = (facept.X(),facept.Y(),facept.Z())
    projpt_facecircle = pyliburo.py3dmodel.construct.make_circle(pyfacept, (0,0,1),5)
    face_circles.append(projpt_facecircle.Edge())
    
displaylist3.extend(face_circles)
displaylist3.append(face2project)
displaylist3.append(face_plane)

projected_pt = pyliburo.py3dmodel.calculate.project_point_on_faceplane(occ_face, pypt)
pyprojpt = (projected_pt.X(), projected_pt.Y(),projected_pt.Z())
projpt_occcircle = pyliburo.py3dmodel.construct.make_circle(pyprojpt, (0,0,1),5)
#create the edge between the origpt and the projpt
projpt_occedge = pyliburo.py3dmodel.construct.make_edge(pypt, pyprojpt)

displaylist1.append(occ_face)
displaylist1.append(projpt_occcircle.Edge())
displaylist1.append(projpt_occedge)

#project point to edge
dest_occedge = pyliburo.py3dmodel.construct.make_edge((50,100,0), (50,20,0))
interedgept =pyliburo.py3dmodel.calculate.project_point_on_infedge(dest_occedge, pypt)
interedgept_occcircle = pyliburo.py3dmodel.construct.make_circle((interedgept.X(), interedgept.Y(), interedgept.Z()), (0,0,1),3)
interedgept_path = pyliburo.py3dmodel.construct.make_edge(pypt, (interedgept.X(), interedgept.Y(), interedgept.Z()))

displaylist2.append(interedgept_path)
displaylist2.append(dest_occedge)
displaylist2.append(interedgept_occcircle.Edge())

#create the 2dlist
display2dlist = []
display2dlist.append(displaylist1)
display2dlist.append(displaylist2)
display2dlist.append(displaylist3)
colour_list = ["WHITE", "BLUE", "RED"]

pyliburo.py3dmodel.construct.visualise(display2dlist, colour_list)