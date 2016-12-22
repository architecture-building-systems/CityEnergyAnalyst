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
import xml.dom.minidom
from xml.dom.minidom import Document
import random
import math
import os

import analyse_xml
#================================================================================
def frange(start, end=None, inc=None):
    """A range function, that does accept float increments..."""
    if end == None:
        end = start + 0.0
        start = 0.0
    else: start += 0.0 # force it to be a float

    if inc == None:
        inc = 1.0
    count = int(math.ceil((end - start) / inc))

    L = [None,] * count

    L[0] = start
    for i in xrange(1,count):
        L[i] = L[i-1] + inc
    return L
    
#================================================================================
#(num_genes, type, (parameters))
#((4, "INT_RANGE", (0,10)),....)
class Gene(object):
    def __init__(self, gene_type, value_range):
        self.gene_type = gene_type
        self.value_range = value_range
        self.position = None
        
class GenotypeMeta(object):
    def __init__(self):
        self.gene_list = []

    def add_gene(self, gene):
        self.gene_list.append(gene)       

    def gene_position(self):
        gene_list = self.gene_list
        cnt = 0
        for g in gene_list:
            g.position = cnt
            cnt = cnt + 1
            
    def length(self):
        length = len(self.gene_list)
        return length

#================================================================================
class Genotype(object):
    def __init__(self, genotype_meta):
        self.genotype_meta = genotype_meta
        self.values = []
        
    def randomise(self):
        genes = self.genotype_meta.gene_list
        for gene in genes:
            gene_type = gene.gene_type
            value_range = gene.value_range
            if gene_type == "float_range":
                gene_range = frange(value_range[0], value_range[1], value_range[2])#random.uniform( value_range[0], value_range[1])
                gene_value = random.choice(gene_range)
                self.values.append(gene_value)
                
            if gene_type == "float_choice":
                gene_value = random.choice(value_range)
                self.values.append(gene_value)
                
            if gene_type == "int_range":
                gene_value = random.randrange(value_range[0], value_range[1], value_range[2])
                self.values.append(gene_value)
                
            if gene_type == "int_choice":
                gene_value = random.choice(value_range)
                self.values.append(gene_value)
        
    def mutate(self, mutation_prob):
        gene_list = self.genotype_meta.gene_list
        
        for c in range(len(gene_list)):
            roll = random.random()
            if roll <= mutation_prob:
                gene_type = None
                value_range = None
                for gene in gene_list:
                    if gene.position == c:
                        gene_type = gene.gene_type
                        value_range = gene.value_range

                if gene_type == "float_range":
                    self.values[c] = random.choice(frange(value_range[0], value_range[1], value_range[2]))
                
                if gene_type == "float_choice":
                    self.values[c] = random.choice(value_range)
                
                if gene_type == "int_range":
                    self.values[c] = random.randrange(value_range[0], value_range[1], value_range[2])
                
                if gene_type == "int_choice":
                    self.values[c] = random.choice(value_range)
                    
    def read_str(self,string):
        self.values = map(float, string.split(" "))

    def write_str(self):
        return " ".join(map(str,self.values))

    def __repr__(self):
        return self.write_str()
#================================================================================      
class DerivedParams(object):
    def __init__(self):
        self.values = []
        
    def add_param(self, param):
        self.values.append(param)

    def length(self):
        length = len(self.values)
        return length
    
    def read_str(self,string):
        self.values = map(float, string.split(" "))

    def write_str(self):
        return " ".join(map(str,self.values))

    def __repr__(self):
        return self.write_str()

#================================================================================      
class Individual(object):
    def __init__(self, idx, genotype_meta, score_meta):
        self.id = idx
        self.genotype_meta = genotype_meta
        self.genotype = Genotype(self.genotype_meta)
        self.live = True
        self.scores = map(lambda x:None, range(score_meta.get_num_scores()))
        self.derivedparams = DerivedParams()
        self.generation = None
        self.distance = 0.0
        self.rank = None
        
    def randomise(self):
        self.genotype.randomise()
        
    def set_score(self, index, score):
        self.scores[index] = score

    def get_score(self, index):
        return self.scores[index]
    
    def is_not_evaluated(self):
        score_list = self.scores
        N_count = score_list.count(None)
        if len(score_list) == N_count:
            return True
        else:
            return False
        
    def add_derivedparams(self, derivedparams):
        dp = self.derivedparams
        dp.values = derivedparams

    def add_generation(self, generation):
        self.generation = generation
        
    def xml(self):
        doc = Document()
        if self.live:
            status = "true"
        else:
            status = "false"
            
        xml_doc = analyse_xml.create_xml_individual(doc, self.id, self.generation, status, self.genotype, self.derivedparams, self.scores)
        return xml_doc.toxml()
        
    def __repr__(self):
        return str(self.id) + "," + str(self.generation) + "," + str(self.genotype) + "," + str(self.derivedparams) + "," + ",".join(map(str,self.scores)) + "\n"
    
#================================================================================
class ScoreMeta(object):
    MIN = 0
    MAX = 1
    def __init__(self, score_names, scores_min_max):
        self.score_names = score_names
        self.scores_min_max = scores_min_max

    def get_num_scores(self):
        return len(self.scores_min_max)

#================================================================================
class Population(object):
    def __init__(self, size, genotype_meta, score_meta, live_xml_filepath, dead_xml_filepath, mutation_prob, crossover_rate):
        self.size = size
        self.genotype_meta = genotype_meta
        self.individuals = []
        self.live_xml_filepath = live_xml_filepath
        self.dead_xml_filepath = dead_xml_filepath
        self.score_meta = score_meta
        self.mutation_prob = mutation_prob
        self.crossover_rate = crossover_rate
        self.num_archived_individuals = 0

    def select_random_inds(self, num_inds):
        copy_inds = self.individuals[:]
        random.shuffle(copy_inds)
        chosen_inds = copy_inds[:num_inds]
        return chosen_inds
    
    #functions for pareto ranking
    def _dominates(self, ind1, ind2):
        equal = True
        score_meta = self.score_meta
        num_scores = score_meta.get_num_scores()
        for i in range(num_scores):
            val1 = ind1.get_score(i)
            val2 = ind2.get_score(i)
            if val1 != val2: equal = False
            if score_meta.scores_min_max[i] == 0:
                if val2 < val1:
                    return False
            elif val2>val1:
                return False
        if equal: return False
        return True

    def _on_pareto_front(self, ind, inds):
        for ind2 in inds:
            if self._dominates(ind2, ind):
                return False
        return True
    
    def _extract_pareto_front(self, inds):
        pareto_front = []
        non_pareto_front = []
        for ind in inds:    
            if self._on_pareto_front(ind, inds):
                pareto_front.append(ind)
            else:
                non_pareto_front.append(ind)
        return pareto_front, non_pareto_front
    
    def rank(self, inds):
        rank = 1
        cnt = 0
        ranked = []        
        
        while len(inds) > 0:
            pareto_front, non_pareto_front = self._extract_pareto_front(inds)
            ranked.append([])
            for ind in pareto_front:
                ind.rank = rank
                ranked[-1].append(ind)
            inds = non_pareto_front
            cnt +=1
            rank += 1
        return ranked
    
    def crowd_distance_assignment(self, individuals):
        num_inds = len(individuals)
        num_score = self.score_meta.get_num_scores()
        #for each objective 
        for i in range(num_score):
            individuals = self.sort_objectives(individuals, i)
            individuals[0].distance = 1E3000 #float("inf")
            individuals[num_inds-1].distance = 1E3000 #float("inf")
            norm = individuals[num_inds-1].scores[i] - individuals[0].scores[i]
            #print individuals[num_inds-1].scores[i], individuals[0].scores[i]
            for j in range(1, num_inds -1):
                #for fronts that have all scores that are 0
                if norm == 0:
                    individuals[j].distance += 0
                else:
                    individuals[j].distance += (individuals[j+1].scores[i] - individuals[j-1].scores[i])/norm
        return individuals
    
    def crowded_comparison(self, ind1, ind2):
        '''
        Compare the two solutions based on crowded comparison.
        '''
        if ind1.rank < ind2.rank:
            return 1
            
        elif ind1.rank > ind2.rank:
            return -1
            
        elif ind1.distance > ind2.distance:
            return 1
            
        elif ind1.distance < ind2.distance:
            return -1
            
        else:
            return 0
    
    def sort_objectives(self, individuals, obj_idx):
        #arrange in ascending order
        for i in range(len(individuals) - 1, -1, -1):
            for j in range(1, i + 1):
                s1 = individuals[j - 1]
                s2 = individuals[j]
                if s1.scores[obj_idx] > s2.scores[obj_idx]:
                    individuals[j-1] = s2
                    individuals[j] = s1
        return individuals
    
    #=========================================================================
    def crossover(self, ind1, ind2, generation):
        g1 = Genotype(self.genotype_meta)
        g2 = Genotype(self.genotype_meta)
        genotype_length = self.genotype_meta.length()
        #print ind1, ind2
        if genotype_length == 2:
            z = 1
        else:
            z = random.randint(1, genotype_length-2)
        
        for i in range(z):
            g1.values.append(ind1.genotype.values[i])
            g2.values.append(ind2.genotype.values[i])
            
        for i in range(z, genotype_length):
            g1.values.append(ind2.genotype.values[i])
            g2.values.append(ind1.genotype.values[i])

        child_ind1 = Individual(self.get_max_id()+1,self.genotype_meta,self.score_meta)
        child_ind1.genotype = g1
        child_ind2 = Individual(self.get_max_id()+2,self.genotype_meta,self.score_meta)
        child_ind2.genotype = g2
        #add the generation
        child_ind1.add_generation(generation)
        child_ind2.add_generation(generation)
        return child_ind1, child_ind2
        
    def reproduce(self, individuals, generation):
        new_pop = []
        for ind in individuals:
            ind.live = False
            
        fronts = self.rank(individuals)
        dist_fronts = []
        for front in fronts:
            dist_front = self.crowd_distance_assignment(front)
            dist_fronts.extend(dist_front)
            
        while len(new_pop) != len(dist_fronts):
            selected_solutions = [None, None]
            while selected_solutions[0] == selected_solutions[1]:
                for i in range(2):
                    s1 = random.choice(dist_fronts)
                    s2 = s1
                    while s1 == s2:
                        s2 = random.choice(dist_fronts)

                    if self.crowded_comparison(s1, s2) > 0:
                        selected_solutions[i] = s1
                        
                    else:
                        selected_solutions[i] = s2

            #individuals reproduce according to crossover rates
            if random.random() < self.crossover_rate:
                child_solution1, child_solution2 = self.crossover(selected_solutions[0], selected_solutions[1], generation)
                
                #mutation occurs when new individual is born
                child_solution1.genotype.mutate(self.mutation_prob)
                child_solution2.genotype.mutate(self.mutation_prob)
                    
                new_pop.append(child_solution1)
                new_pop.append(child_solution2)
                self.individuals.append(child_solution1)
                self.individuals.append(child_solution2)

    def get_max_id(self):
        #read the dead xml and count the number of individuals in it
        deaddoc = xml.dom.minidom.parse(self.dead_xml_filepath)
        dead_individuals = deaddoc.getElementsByTagName("individual")
        self.num_archived_individuals = len(dead_individuals)
        return self.num_archived_individuals + len(self.individuals) - 1
        
    def randomise(self):
        for i in range(self.size):
            individual = Individual(i, self.genotype_meta, self.score_meta)
            individual.randomise()
            self.individuals.append(individual)
            
    def write(self):
        #check if the dead xml file is empty or not
        if os.stat(self.dead_xml_filepath)[6] == 0:
            deaddoc = Document()
            dead_root_node = deaddoc.createElement("data")
            deaddoc.appendChild(dead_root_node)
            dead_population = deaddoc.createElement("population")
            dead_root_node.appendChild(dead_population)
            
        #the xml file is not empty so do not need to reconstruct the whole xml file     
        else:
            #read the whole xml file and append all the neccessary data into it 
            deaddoc = xml.dom.minidom.parse(self.dead_xml_filepath)

        #always overwrite the live xml file
        doc = Document()
        root_node = doc.createElement("data")
        doc.appendChild(root_node)
        population = doc.createElement("population")
        root_node.appendChild(population)
            
        for ind in self.individuals:
            if ind.live:
                doc = analyse_xml.create_xml_file(doc, ind, "true")
            else:
                #create the status
                deaddoc = analyse_xml.create_xml_file(deaddoc, ind, "false") 
                
        f = open(self.live_xml_filepath,"w")
        f.write(doc.toxml())
        f.close()

        df = open(self.dead_xml_filepath,"w")
        df.write(deaddoc.toxml())
        df.close()
    
    def read(self):
        #read all the individuals that is alive
        doc = xml.dom.minidom.parse(self.live_xml_filepath)
        #get all the individuals
        for individual in doc.getElementsByTagName("individual"):
            identity = analyse_xml.get_childnode_value("identity", individual)
            ind = Individual(int(identity),self.genotype_meta, self.score_meta)
            #add the generation of the individual
            generation = analyse_xml.get_childnode_value("generation", individual)
            ind.add_generation(int(generation))
            #read all the genes and put it into the class
            gene_list = self.genotype_meta.gene_list
            genotype_list  = analyse_xml.get_childnode_values("inputparam", individual)
            genotype_list_converted = []
            print genotype_list, identity
            for cnt in range(len(genotype_list)):
                gene_type = None
                for gene in gene_list:
                    if gene.position == cnt:
                        gene_type = gene.gene_type
                if gene_type == "float_range":
                    genotype_list_converted.append(float(genotype_list[cnt]))
                
                if gene_type == "float_choice":
                    genotype_list_converted.append(float(genotype_list[cnt]))
                
                if gene_type == "int_range":
                    genotype_list_converted.append(int(genotype_list[cnt]))
            
                if gene_type == "int_choice":
                    genotype_list_converted.append(int(genotype_list[cnt]))
                    
            ind.genotype.values = genotype_list_converted
            #read all the derived parameters and put it into the class
            if len(individual.getElementsByTagName("derivedparam"))!=0:
                derived_params = analyse_xml.get_childnode_values("derivedparam", individual)
                derived_params_converted = []
                for dp in derived_params:
                    derived_params_converted.append(float(dp))
                ind.add_derivedparams(derived_params_converted)
            #read all the scores and put it into the class
            if len(individual.getElementsByTagName("score"))!=0:
                scores = analyse_xml.get_childnode_values("score", individual)
                for score_count in range(self.score_meta.get_num_scores()):
                    score_str = scores[score_count]
                    if score_str != "None":
                        ind.set_score(score_count, float(score_str))
                
            self.individuals.append(ind)
                
        #read the dead xml and count the number of individuals in it
        deaddoc = xml.dom.minidom.parse(self.dead_xml_filepath)
        dead_individuals = deaddoc.getElementsByTagName("individual")
        self.num_archived_individuals = len(dead_individuals)
        
    def __repr__(self):
        string = ""
        for ind in self.individuals:
            string = string + str(ind) + "\n"
        return string