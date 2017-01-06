import pyliburo
from collada import *

display2dlist = []
displaylist = []

#dae_file = "F:\\kianwee_work\\smart\\may2016-oct2016\\pycollada_testout\\dae\\simple_case.dae"
#dae_file = "F:\\kianwee_work\\smart\\journal\\mdpi_sustainability\\case_study\\dae\\grid_tower.dae"
dae_file = "F:\\kianwee_work\\smart\\may2016-oct2016\\pycollada_testout\\dae\\complex_surface.dae"
mesh = Collada(dae_file)
unit = mesh.assetInfo.unitmeter or 1
geoms = mesh.scene.objects('geometry')
geoms = list(geoms)
print len(geoms)
g_cnt = 0
for geom in geoms:   
    print geom
    prim2dlist = list(geom.primitives())
    for primlist in prim2dlist:     
        print primlist
        if primlist:
            for prim in primlist:
                if type(prim) == polylist.Polygon or type(prim) == triangleset.Triangle:
                    
                    pyptlist = prim.vertices.tolist()
                    occpolygon = pyliburo.py3dmodel.construct.make_polygon(pyptlist)
                    pyliburo.py3dmodel.fetch.is_face_null(occpolygon)
                    if not pyliburo.py3dmodel.fetch.is_face_null(occpolygon):
                        displaylist.append(occpolygon)
                    g_cnt +=1
                elif type(prim) == lineset.Line:
                    pyptlist = prim.vertices.tolist()
                    occpolygon = pyliburo.py3dmodel.construct.make_edge(pyptlist[0], pyptlist[1])
                    #displaylist.append(occpolygon)
                    g_cnt +=1
            
display2dlist.append(displaylist)
colourlist = ["WHITE"]

pyliburo.py3dmodel.construct.visualise(display2dlist, colourlist)