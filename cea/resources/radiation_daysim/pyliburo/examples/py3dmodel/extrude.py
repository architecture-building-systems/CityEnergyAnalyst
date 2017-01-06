import pyliburo

display_list = []
points1 = [(50,100,0), (75,75,0), (75,60,0),(100,60,0),(100,50,0), (50,0,0),(0,50,0)]#clockwise
points2 = [(60,50,0), (50,75,0),(40,50,0),(50,40,0)]#counterclockwise
points3 = [(50,40,0),(40,50,0),(30,40,0),(40,40,0)]
points4 = [(60,30,0),(70,30,0),(70,40,0),(60,40,0)]

face1 = pyliburo.py3dmodel.construct.make_polygon(points1)
extrude1 = pyliburo.py3dmodel.construct.extrude(face1, (0,0,1), 50)
ext1_faces = pyliburo.py3dmodel.fetch.faces_frm_solid(extrude1)
mext1_faces = []
for ext1_face in ext1_faces:
    srf_dir = pyliburo.py3dmodel.calculate.face_normal(ext1_face)
    srf_midpt = pyliburo.py3dmodel.calculate.face_midpt(ext1_face)
    loc_pt = pyliburo.py3dmodel.modify.move_pt(srf_midpt, srf_dir, 5)
    mext1_face = pyliburo.py3dmodel.modify.move(srf_midpt, loc_pt, ext1_face)
    mext1_faces.append(mext1_face)
    
face2 = pyliburo.py3dmodel.construct.make_polygon(points2)
extrude2 = pyliburo.py3dmodel.construct.extrude(face2, (0,0,1), 80)

min_dist = pyliburo.py3dmodel.calculate.minimum_distance(extrude1, extrude2)

display2dlist = []
display2dlist.append(mext1_faces)
pyliburo.py3dmodel.construct.visualise(display2dlist, ["WHITE"])