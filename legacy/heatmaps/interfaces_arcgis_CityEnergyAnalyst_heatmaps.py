# this file contains the CeaTool definition for the arcgis interface - it is now retired

class HeatmapsTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'heatmaps'
        self.label = 'Heatmaps'
        self.description = 'Generate maps representing hot and cold spots of energy consumption'
        self.category = 'Visualization'
        self.canRunInBackground = False

    def override_parameter_info(self, parameter_info, parameter):
        if parameter.name == 'file-to-analyze':
            parameter_info.datatype = "String"
            parameter_info.filter.list = []
        elif parameter.name == 'analysis-fields':
            parameter_info.datatype = 'String'
            parameter_info.multiValue = True
            parameter_info.parameterDependencies = ['file-to-analyze']
        return parameter_info

    def updateParameters(self, parameters):
        super(HeatmapsTool, self).updateParameters(parameters)
        parameters = dict_parameters(parameters)
        locator = cea.inputlocator.InputLocator(parameters['general:scenario'].valueAsText)
        file_names = [os.path.basename(locator.get_total_demand())]
        file_names.extend(
            [f for f in os.listdir(locator.get_lca_emissions_results_folder())
             if f.endswith('.csv')])
        file_to_analyze = parameters['heatmaps:file-to-analyze']
        if not file_to_analyze.value or file_to_analyze.value not in file_names:
            file_to_analyze.filter.list = file_names
            file_to_analyze.value = file_names[0]
        # analysis_fields
        analysis_fields = parameters['heatmaps:analysis-fields']
        if file_to_analyze.value == file_names[0]:
            file_path = locator.get_total_demand()
        else:
            file_path = os.path.join(locator.get_lca_emissions_results_folder(),
                                     file_to_analyze.value)
        import pandas as pd
        df = pd.read_csv(file_path)
        fields = df.columns.tolist()
        fields.remove('Name')
        analysis_fields.filter.list = list(fields)

    def execute(self, parameters, _):
        param_dict = dict_parameters(parameters)
        scenario = param_dict['general:scenario'].valueAsText
        file_path = param_dict['heatmaps:file-to-analyze'].valueAsText
        locator = cea.inputlocator.InputLocator(scenario)
        if file_path == os.path.basename(locator.get_total_demand()):
            file_path = locator.get_total_demand()
        else:
            file_path = os.path.join(locator.get_lca_emissions_results_folder(), file_path)
        param_dict['heatmaps:file-to-analyze'].value = file_path
        super(HeatmapsTool, self).execute(parameters, _)