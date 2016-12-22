import pyliburo

points1 = [(50,100,0), (75,75,0), (75,60,0),(100,60,0),(100,50,0), (50,0,0),(0,50,0)]
face1 = pyliburo.py3dmodel.construct.make_polygon(points1)

points2 = 
extrude1 = pyliburo.py3dmodel.construct.extrude(face1, (0,0,1), 50)
ext1_faces = pyliburo.py3dmodel.fetch.faces_frm_solid(extrude1)
shell = pyliburo.py3dmodel.construct.make_shell_frm_faces([face1])
print shell

is_closed = pyliburo.py3dmodel.calculate.is_shell_closed(shell)

display2dlist = []
display2dlist.append([shell])
pyliburo.py3dmodel.construct.visualise(display2dlist, ["WHITE"])