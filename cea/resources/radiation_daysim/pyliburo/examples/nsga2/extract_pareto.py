import pyliburo

print "READING XML ..."
livexmlfile = "F:\\kianwee_work\\smart\\case_studies\\5x5ptblks\\nsga2_xml\\archive\\live.xml"
deadxmlfile = "F:\\kianwee_work\\smart\\case_studies\\5x5ptblks\\nsga2_xml\\archive\\dead.xml"
overallxmlfile = "F:\\kianwee_work\\smart\\case_studies\\5x5ptblks\\nsga2_xml\\archive\\overall.xml"
pyliburo.pyoptimise.analyse_xml.combine_xml_files(livexmlfile, deadxmlfile,overallxmlfile)
pyliburo.pyoptimise.analyse_xml.rmv_unevaluated_inds(overallxmlfile)
inds = pyliburo.pyoptimise.analyse_xml.get_inds_frm_xml(overallxmlfile)

print "EXTRACTING PARETO ..."
pfront, nonpfront = pyliburo.pyoptimise.analyse_xml.extract_pareto_front(inds, [1,1])
pareto_pts = []
pareto_labellist =[]
pareto_arealist = []
pareto_colourlist = []
for pind in pfront:
    score_list = pyliburo.pyoptimise.analyse_xml.get_score(pind)
    idx = pyliburo.pyoptimise.analyse_xml.get_id(pind)
    pareto_pts.append(score_list)
    pareto_labellist.append(idx)
    pareto_arealist.append(300)
    pareto_colourlist.append("red")
    
npareto_pts = []
npareto_labellist = []
npareto_arealist = []
npareto_colourlist = []
for upind in nonpfront:
    score_list = pyliburo.pyoptimise.analyse_xml.get_score(upind)
    idx = pyliburo.pyoptimise.analyse_xml.get_id(upind)
    npareto_pts.append(score_list)
    npareto_labellist.append("")
    npareto_arealist.append(10)
    npareto_colourlist.append("black")

print "DRAWING GRAPH ..."
pts2plotlist = []
pts2plotlist.extend(pareto_pts)  
pts2plotlist.extend(npareto_pts)
label_list = []
label_list.extend(pareto_labellist) 
label_list.extend(npareto_labellist) 
colourlist = []
colourlist.extend(pareto_colourlist)
colourlist.extend(npareto_colourlist)
arealist = []
arealist.extend(pareto_arealist)
arealist.extend(npareto_arealist)

filepath = "F:\\kianwee_work\\smart\\conference\\bs2017\\image\\png\\pareto_front.png"
pyliburo.pyoptimise.draw_graph.scatter_plot(pts2plotlist, colourlist, arealist, label_size=24, labellist = label_list,
                                            xlabel = "FAR", ylabel = "DFAI (%)", savefile = filepath )
#pyliburo.pyoptimise.draw_graph.scatter_plot_label(pts2plotlist, colourlist, labellist, arealist)
print len(pareto_pts), len(npareto_pts)