import time
import os
import pyliburo

#specify the citygml file
current_path = os.path.dirname(__file__)
parent_path = os.path.abspath(os.path.join(current_path, os.pardir))

#================================================================================
#INSTRUCTION: SPECIFY THE CITYGML FILE
#================================================================================
citygml_filepath = "F:\\kianwee_work\\smart\\conference\\asim2016\\asim_example\\citygml\\punggol_citygml_asim_origlvl.gml"
#change the filepath to where you want to save the file to 
image_file = "F:\\kianwee_work\\smart\\conference\\asim2016\\asim_example\\citygml\\rpvp\\result.png"
falsecolour_file = "F:\\kianwee_work\\smart\\conference\\asim2016\\asim_example\\citygml\\rpvp\\falsecolour.png"
#specify weatherfilepath
weatherfilepath = "F:\\kianwee_work\\spyder_workspace\\envuo\\examples\\punggol_case_study\\weatherfile\\SGP_Singapore.486980_IWEC.epw"
#specify the grid size
xdim = 3
ydim = 3

#================================================================================
#INSTRUCTION: SPECIFY THE CITYGML FILE
#================================================================================
time1 = time.clock()
print "EVALUATING MODEL ... ..."

evaluations = pyliburo.citygml2eval.Evals(citygml_filepath)
irrad_threshold = 1280 #kwh/m2
pvai, pv_potential, irrad_res, topo_list,high_irrad_area = evaluations.pvai(irrad_threshold, weatherfilepath,xdim,ydim, surface = "roof")
print "PVRAI:", pvai
print "HIGH ROOF IRRAD AREA:", high_irrad_area
print "ROOF PV POTENTIAL:", pv_potential

evaluations2 = pyliburo.citygml2eval.Evals(citygml_filepath)
irrad_threshold = 512 #kwh/m2
pvai, pv_potential, irrad_res, topo_list,high_irrad_area = evaluations2.pvai(irrad_threshold, weatherfilepath,xdim,ydim, surface = "facade")
print "PVFAI:", pvai
print "HIGH FACADE IRRAD AREA:", high_irrad_area
print "FACADE PV POTENTIAL:", pv_potential


time2 = time.clock()
print "TIME TAKEN FOR EVALUATION", (time2-time1)/60
print "MODEL EVALUATED!"


'''
print "VISUALISING RESULT"
print "ROOF PV POTENTIAL:" + str(pv_potential) + "kWh/yr"
envuo.py3dmodel.construct.visualise_falsecolour_topo(irrad_res, topo_list, falsecolour_file, image_file, [evaluations.facade_occfaces],["WHITE"])
time3 = time.clock()
print "TIME TAKEN", (time3-time1)/60
print "VISUALISED"
'''