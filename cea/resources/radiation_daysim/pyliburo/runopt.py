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
import pyoptimise

def empty_xml_files(xml_filelist):
    for xmlf in xml_filelist:
        open(xmlf,"w").close()
        
def create_population_class(gene_dict_list, score_dict_list, mutation_rate,crossover_rate,init_population,
          live_file,dead_file):
    #====================================
    #initialise the genotype class object
    #====================================
    gm = pyoptimise.nsga2.GenotypeMeta()
    #====================================
    #get the gene meta setting 
    #====================================
    '''
    4 types of genes 
    float_range
    float_choice
    int_range
    int_choice
    '''
    for gene_dict in gene_dict_list:
        gene_type = gene_dict["type"]
        gene_range = gene_dict["range"]
        gene = pyoptimise.nsga2.Gene(gene_type, gene_range)
        gm.add_gene(gene)
    gm.gene_position()
    #====================================
    #score meta
    #====================================
    #initiate the score meta class
    score_m_list = []
    score_name_list = []
    for score_dict in score_dict_list:
        score_name = score_dict["name"]
        score_name_list.append(score_name)
        score_minmax = score_dict["minmax"]
        if score_minmax == "min":
            score_m_list.append(pyoptimise.nsga2.ScoreMeta.MIN)
        if score_minmax == "max":
            score_m_list.append(pyoptimise.nsga2.ScoreMeta.MAX)

    sm = pyoptimise.nsga2.ScoreMeta(score_name_list, score_m_list)
    #====================================
    #population class parameters
    #====================================
    
    p = pyoptimise.nsga2.Population(init_population, gm, sm, live_file , dead_file, mutation_rate, crossover_rate)
    return p

def initialise_nsga2(gene_dict_list, score_dict_list, mutation_rate,crossover_rate,init_population,
          live_file,dead_file ):
              
    empty_xml_files([live_file, dead_file])
    p = create_population_class(gene_dict_list, score_dict_list, mutation_rate,crossover_rate,init_population,
          live_file,dead_file)
    p.randomise()
    not_evaluated = p.individuals
    for ind in not_evaluated:
        ind.add_generation(0)
        
    p.write()
    return p
    
def resume_nsga2(gene_dict_list, score_dict_list, mutation_rate,crossover_rate,init_population,
      live_file,dead_file ):
              
    p = create_population_class(gene_dict_list, score_dict_list, mutation_rate,crossover_rate,init_population,
          live_file,dead_file)
          
    p.read()       
    return p

def feedback_nsga2(population):
    #===================================
    #feedback
    #=================================== 
    current_gen = population.individuals[0].generation
    population.reproduce(population.individuals, current_gen+1)
    population.write()
    #====================================
    #separate the evaluated individuals from the unevaluated one  
    #====================================
    unevaluated = []
    for ind in population.individuals:
        if ind.live == True:
            unevaluated.append(ind)
            
    population.individuals = unevaluated
