# ==================================================================================================
#
#    Copyright (c) 2016, Chen Kian Wee (chenkianwee@gmail.com)
#
#    This file is part of pyliburo
#
#    pyliburo is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    pyliburo is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Dexen.  If not, see <http://www.gnu.org/licenses/>.
#
# ==================================================================================================
from xml.dom.minidom import Node
import xml.dom.minidom
from xml.dom.minidom import Document
#================================================================================
#xml functions
#================================================================================
def findmedian(lst):
    sortedLst = sorted(lst)
    lstLen = len(lst)
    index = (lstLen - 1) // 2

    if (lstLen % 2):
        return sortedLst[index]
    else:
        return (sortedLst[index] + sortedLst[index + 1])/2.0
        
def get_childnode_values(node_name, parent_node):
    values = []
    for node in parent_node.getElementsByTagName(node_name):
        node_value = ""
        for cnode in node.childNodes:
            if cnode.nodeType == Node.TEXT_NODE:
                #in case the text node is separated 
                tvalue = str(cnode.nodeValue)
                node_value = node_value + tvalue
                
        values.append(node_value)
                
    return values

def get_childnode_attributes(node_name, parent_node, attribute_name):
    attributes = []
    for node in parent_node.getElementsByTagName(node_name):
        attributes.append(str(node.attributes[attribute_name].value))

    return attributes

def get_childnode_value(node_name, parent_node):
    nodes_list = parent_node.getElementsByTagName(node_name)
    num_nodes = len(nodes_list)
    
    if num_nodes > 1:
        raise Exception("more than one node!!")
    elif num_nodes == 0:
        raise Exception("no nodes!!")
    else:
        values = []
        for node in nodes_list:
            node_value = ""
            for cnode in node.childNodes:
                if cnode.nodeType == Node.TEXT_NODE:
                    #in case the text node is separated 
                    tvalue = str(cnode.nodeValue)
                    node_value = node_value + tvalue
            values.append(node_value)
            
    return values[0]

def edit_nodevalue(node_name, parent_node, change_value):
    nodes_list = parent_node.getElementsByTagName(node_name)
    num_nodes = len(nodes_list)
    
    if num_nodes > 1:
        raise Exception("more than one node!!")
    elif num_nodes == 0:
        raise Exception("no nodes!!")
    else:
        for node in nodes_list:
            for cnode in node.childNodes:
                if cnode.nodeType == Node.TEXT_NODE:
                    cnode.nodeValue = change_value
                    
def create_childnode(node_name, parent_node, value, doc):
    childnode = doc.createElement(node_name)
    value = doc.createTextNode(value)
    childnode.appendChild(value)
    parent_node.appendChild(childnode)

def create_xml_file(doc, ind, status):
    population = doc.getElementsByTagName("population")[0]
    #create the individual 
    individual = doc.createElement("individual")
    population.appendChild(individual)
    #create the identity
    create_childnode("identity", individual, str(ind.id), doc)
    #create the generation
    create_childnode("generation", individual, str(ind.generation), doc)
    #create the status
    create_childnode("status", individual, status, doc)
    #create input params
    inputparams = doc.createElement("inputparams")
    individual.appendChild(inputparams)
    #create inputparam
    #get all the genotype value
    for gen_value in ind.genotype.values:
        if isinstance(gen_value, float):
            create_childnode("inputparam", inputparams, str(round(gen_value, 5)),doc)
        elif isinstance(gen_value, int):
            create_childnode("inputparam", inputparams, str(gen_value),doc)
    #create derived params
    derivedparams = doc.createElement("derivedparams")
    individual.appendChild(derivedparams)
    #create derivedparam
    if len(ind.derivedparams.values) != 0:
        for derived_value in ind.derivedparams.values:
            create_childnode("derivedparam", derivedparams, str(derived_value), doc)
    #create scores
    scores = doc.createElement("scores")
    individual.appendChild(scores)
    #create score
    if ind.is_not_evaluated() == False:
        for score_value in ind.scores:
            create_childnode("score", scores, str(round(score_value, 3)),doc)
    return doc

def create_xml_individual(doc, identity, generation, status, genotype, ind_derivedparams, ind_scores ):
    #create the individual 
    individual = doc.createElement("individual")
    doc.appendChild(individual)
    #create the identity
    create_childnode("identity", individual, str(identity), doc)
    #create the generation
    create_childnode("generation", individual, str(generation), doc)
    #create the status
    create_childnode("status", individual, status, doc)
    #create input params
    inputparams = doc.createElement("inputparams")
    individual.appendChild(inputparams)
    #create inputparam
    #get all the genotype value
    for gen_value in genotype.values:
        if isinstance(gen_value, float):
            create_childnode("inputparam", inputparams, str(round(gen_value,5)),doc)
        elif isinstance(gen_value, int):
            create_childnode("inputparam", inputparams, str(gen_value),doc)
    #create derived params
    derivedparams = doc.createElement("derivedparams")
    individual.appendChild(derivedparams)
    #create derivedparam
    if len(ind_derivedparams.values) != 0:
        for derived_value in ind_derivedparams.values:
            create_childnode("derivedparam", derivedparams, str(round(derived_value,3)), doc)
    #create scores
    scores = doc.createElement("scores")
    individual.appendChild(scores)
    #create score
    if ind_scores.count(None) == 0:
        for score_value in ind_scores:
            create_childnode("score", scores, str(round(score_value,3)),doc)
    return doc
    
def get_score(ind):
    score_list = get_childnode_values("score", ind)
    score_list_f = []
    for score in score_list:
        score_list_f.append(float(score))
    return score_list_f
    
def get_id(ind):
    identity = get_childnode_value("identity", ind)
    return identity

def get_inds_frm_xml(xml_filepath):
    doc = xml.dom.minidom.parse(xml_filepath)
    ind_list = doc.getElementsByTagName("individual")
    return ind_list

def write_inds_2_xml(inds, res_path):
    #write an xml file
    doc = Document()
    root_node = doc.createElement("data")
    doc.appendChild(root_node)
    population = doc.createElement("population")
    root_node.appendChild(population)

    doc = xml.dom.minidom.parseString("<data><population></population></data>")
    parent_node = doc.getElementsByTagName("population")[0]
    
    for ind_node in inds:
        parent_node.appendChild(ind_node)
        
    f = open(res_path,"w")
    f.write(doc.toxml())
    f.close()
    
def combine_xml_files(xmlfile1, xmlfile2, resxml_file):
    total_inds = []
    inds1 = get_inds_frm_xml(xmlfile1)
    inds2 = get_inds_frm_xml(xmlfile2)
    total_inds.extend(inds1)
    total_inds.extend(inds2)
    write_inds_2_xml(total_inds, resxml_file)

def rmv_unevaluated_inds(xmlfile):
    eval_inds = []
    inds = get_inds_frm_xml(xmlfile)
    for ind in inds:
        scorelist = get_score(ind)
        if scorelist:
            eval_inds.append(ind)
            
    write_inds_2_xml(eval_inds, xmlfile)
        
def dominates(ind1, ind2, min_max_list):
    equal = True
    score1 = get_score(ind1)
    score2 = get_score(ind2)
    num_scores = len(score1)
    for i in range(num_scores):
        #print ind1
        #print ind2
        val1 = score1[i]
        val2 = score2[i]
        if val1 != val2: equal = False
        if min_max_list[i] == 0:
            if val2 < val1:
                return False
        elif val2>val1:
            return False
    if equal: return False
    return True

def on_pareto_front(ind, inds, min_max_list):
    for ind2 in inds:
        if dominates(ind2, ind, min_max_list):
            return False
    return True
    
def extract_pareto_front(inds, min_max_list):
    '''
    min_max_list = [0,1]
    0 = min
    1 = max
    '''
    pareto_front = []
    non_pareto_front = []
    for ind in inds:
        if (len(get_score(ind))-1) !=0:     
            if on_pareto_front(ind, inds, min_max_list):
                pareto_front.append(ind)
            else:
                non_pareto_front.append(ind)
    return pareto_front, non_pareto_front