import pyliburo

displaylist1 = []
displaylist2 = []

#point for projection
pypt = (0,0,0)
occ_origcircle = pyliburo.py3dmodel.construct.make_circle(pypt, (0,0,1),5)

#face for projection or intersection
pyptlist = [(50,100,0), (75,60,0), (75,60,50),(50,100,60)]#clockwise
pyptlist = [(0,0,0), (5,0,0), (5,5,0),(0,5,0)]#clockwise
occ_face = pyliburo.py3dmodel.construct.make_polygon(pyptlist)
displaylist1.append(occ_face)

#intersect edge with face
#define an edge
dest_pypt = (5,5,0)
occ_edge = pyliburo.py3dmodel.construct.make_edge(pypt, dest_pypt)
displaylist1.append(occ_edge)
interss = pyliburo.py3dmodel.calculate.intersect_edge_with_face(occ_edge, occ_face)
print interss
if interss:
    pyinterpt = (interss[0].X(),interss[0].Y(),interss[0].Z())
    interss_occcircle = pyliburo.py3dmodel.construct.make_circle(pyinterpt, (0,0,1),3)
    displaylist1.append(interss_occcircle)

#specify a point and a direction and it will intersect anything thats along the path
occ_interpt, occ_interface = pyliburo.py3dmodel.calculate.intersect_shape_with_ptdir(occ_face, pypt, (1,1,0))

if occ_interpt != None:
    interpt_occcircle = pyliburo.py3dmodel.construct.make_circle((occ_interpt.X(),occ_interpt.Y(),occ_interpt.Z()), (0,0,1),3)
    displaylist2.append(interpt_occcircle)
    displaylist2.append(occ_interface)
    interpath = pyliburo.py3dmodel.construct.make_edge(pypt, (occ_interpt.X(),occ_interpt.Y(),occ_interpt.Z()))
    displaylist2.append(interpath)

#create the 2dlist
display2dlist = []
display2dlist.append(displaylist1)
#display2dlist.append(displaylist2)
colour_list = ["WHITE"]

pyliburo.py3dmodel.construct.visualise(display2dlist, colour_list)