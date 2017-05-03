import cea.inputlocator
import pickle

trace_data = pickle.load(file=open('C:/Users/Bhargava/Documents/GitHub/CEAforArcGIS/docs/scenario_folder/emissions.trace.pickle', 'r'))
all_nodes = set(td[1].fqname for td in trace_data if not td[0].fqname.startswith('cea.inputlocator.InputLocator'))
locator_funcs = [n for n in all_nodes if n.startswith('cea.inputlocator.InputLocator')]
file_names = [eval(f).__doc__ for f in locator_funcs]

print (file_names)