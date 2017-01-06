import time
import os
import pyliburo

#specify the citygml file
current_path = os.path.dirname(__file__)
parent_path = os.path.abspath(os.path.join(current_path, os.pardir))
#citygml_filepath = os.path.join(parent_path, "punggol_case_study", "citygml", "punggol_luse5.gml")
citygml_filepath = "F:\\kianwee_work\\smart\\case_studies\\5x5ptblks\\3238.gml"

#change the filepath to where you want to save the file to 
image_file = "F:\\kianwee_work\\spyder_workspace\\pyliburo\\examples\\punggol_case_study\\citygml\\py2radiance_data\\result.png"
falsecolour_file = "F:\\kianwee_work\spyder_workspace\pyliburo\examples\punggol_case_study\citygml\\py2radiance_data\\falsecolour.png"

evaluations = pyliburo.citygml2eval.Evals(citygml_filepath)
xdim = 9
ydim = 9
weatherfilepath = os.path.join(parent_path, "punggol_case_study", "weatherfile", "SGP_Singapore.486980_IWEC.epw")

time1 = time.clock()
print "EVALUATING MODEL ... ..."

'''
irrad_threshold (kwh/m2)
50w/m2 is the benchmark envelope thermal transfer value for spore greenmark basic for commercial buildings
its calculated as an hourly average, multiplying it by 8760 hrs, we get the rough value for the permissible annual solar heat gain
1.5 is a factor to account for the raw irradiation falling on the surface, the higher we assume the better your envelope quality. 
factor of 1.5 means we expect 60% of the heat to be transmitted through the envelope 
'''

irrad_threshold = (50*8760*1.5)/1000.0
sgfai, topo_list, irrad_ress  = evaluations.sgfai(irrad_threshold,weatherfilepath,xdim,ydim)
print "SOLAR GAIN FACADE AREA INDEX:", sgfai

'''
illum threshold (lux)
'''

illum_threshold = 10000
dfai, topo_list, illum_ress = evaluations.dfai(illum_threshold,weatherfilepath,xdim,ydim)
print "DAYLIGHT FACADE AREA INDEX:", dfai

'''
solar potential measures the potential energy that can be generated on the building surfaces
'''

irrad_threshold = 1280 #kwh/m2
pvrai, rpv_potential, irrad_res, topo_list, high_irrad_area = evaluations.pvai(irrad_threshold, weatherfilepath,xdim,ydim, surface = "roof")

irrad_threshold = 512 #kwh/m2
pvfai, fpv_potential, irrad_res, topo_list,high_irrad_area = evaluations.pvai(irrad_threshold, weatherfilepath,xdim,ydim, surface = "facade")
print "PV ROOF AREA INDEX :", pvrai
print "PV FACADE AREA INDEX :", pvfai


time2 = time.clock()
print (time2-time1)/60
print "MODEL EVALUATED!"

print "VISUALISING RESULT"

pyliburo.py3dmodel.construct.visualise_falsecolour_topo(illum_ress, topo_list, falsecolour_file, image_file)
time3 = time.clock()
print "TIME TAKEN", (time3-time1)/60
print "VISUALISED"
