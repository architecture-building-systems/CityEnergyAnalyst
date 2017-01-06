import pyliburo
xml_filepath = "F:\\kianwee_work\\smart\\case_studies\\5x5ptblks\\nsga2_xml\\archive\\overall.xml"
res1 = "F:\\kianwee_work\\smart\\case_studies\\5x5ptblks\\nsga2_xml\\archive\\density_3.8_3.9.xml"
res2 = "F:\\kianwee_work\\smart\\case_studies\\5x5ptblks\\nsga2_xml\\archive\\dfai_91.5.xml"
inds = pyliburo.pyoptimise.analyse_xml.get_inds_frm_xml(xml_filepath)

target_density_inds = []
target_dfai_inds = []
for ind in inds:
    score_list = pyliburo.pyoptimise.analyse_xml.get_score(ind)
    density = score_list[0]
    dfai = score_list[1]
    if density == 3.841:
        target_density_inds.append(ind)
        if dfai>91 and dfai<93:
            idx = pyliburo.pyoptimise.analyse_xml.get_id(ind)
            print idx
            target_dfai_inds.append(ind)
            
pyliburo.pyoptimise.analyse_xml.write_inds_2_xml(target_density_inds, res1)
pyliburo.pyoptimise.analyse_xml.write_inds_2_xml(target_dfai_inds, res2)