import time
import os
import pyliburo

#specify the citygml file
current_path = os.path.dirname(__file__)
parent_path = os.path.abspath(os.path.join(current_path, os.pardir))
citygml_filepath = os.path.join(parent_path, "punggol_case_study", "citygml", "punggol_citygml_asim.gml")

displaylist = []
displaylist2 = []
evaluations = pyliburo.citygml2eval.Evals(citygml_filepath)

time1 = time.clock()
print "EVALUATING MODEL ... ..."
wind_dir = (1,1,0)
avg_fai, fuse_psrfs_list, surfaces_projected_list = evaluations.fai(wind_dir)

time2 = time.clock()
print (time2-time1)/60
print avg_fai

displaylist2.extend(fuse_psrfs_list)
displaylist.extend(surfaces_projected_list)

display2dlist = []
display2dlist.append(displaylist)
display2dlist.append(displaylist2)
colour_list = ["BLUE", "RED"]

pyliburo.py3dmodel.construct.visualise(display2dlist, colour_list)