
import functools
import os
import pandas as pd
import cea.inputlocator

"""
This SUperCalss is applied to all the plots in this catgory. Consider it as a Global.
"""

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2023, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Jimeno Fonseca"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

#Part I: Define a plot Category
label = 'my_category'

#Part II. refactor the name of this Class
class MyCategoryPlotBase(cea.plots.PlotBase):

    #Part III. Define category name
    #Example
    category_name = "my_category"

    #Part IV. Define what parameters to show in the dashboard
    #Example:
    expected_parameters = {
        'buildings': 'plots:buildings',
        'scenario-name': 'general:scenario-name',
        'timeframe': 'plots:timeframe',
        'normalization': 'plots-schedules:normalization',
    }

    # Part V. Define what are the local inputs of the plots (files as well as variables)
    # just need to follow this format since we are working a superclass
    # Example:
    def __init__(self, project, parameters, cache):
        super(MyCategoryPlotBase, self).__init__(project, parameters, cache)
        self.category_path = os.path.join('new_basic', 'my_category')
        self.normalization = self.parameters['normalization']
        self.input_files = [(self.locator.get_schedule_model_file, [building]) for building in self.buildings]
        self.weather = self.locator.get_weather_file()
        self.schedule_analysis_fields = ['people_p',
                                      'Vww_lph',
                                      'Vw_lph',
                                      'Ql_W',
                                      'Qs_W',
                                      'Ea_W',
                                      'El_W',
                                      'Ed_W',
                                      'Qcpro_W',
                                      'Epro_W',
                                      'Qcre_W',
                                      'Qhpro_W',
                                         ]

    #Part VI. Define functions that can help to clean the data, normalize it etc. before it goes in the right format for plotting.
    def normalize_data(self, data_processed, buildings, analysis_fields):
        if self.normalization == "gross floor area":
            data = pd.read_csv(self.locator.get_total_demand()).set_index('Name')
            normalizatioon_factor = data.loc[buildings]['GFA_m2'].sum()
            data_processed = data_processed.apply(
                lambda x: x / normalizatioon_factor if x.name in analysis_fields else x)
        elif self.normalization == "net floor area":
            data = pd.read_csv(self.locator.get_total_demand()).set_index('Name')
            normalizatioon_factor = data.loc[buildings]['Aocc_m2'].sum()
            data_processed = data_processed.apply(
                lambda x: x / normalizatioon_factor if x.name in analysis_fields else x)
        elif self.normalization == "air conditioned floor area":
            data = pd.read_csv(self.locator.get_total_demand()).set_index('Name')
            normalizatioon_factor = data.loc[buildings]['Af_m2'].sum()
            data_processed = data_processed.apply(
                lambda x: x / normalizatioon_factor if x.name in analysis_fields else x)
        elif self.normalization == "building occupancy":
            data = pd.read_csv(self.locator.get_total_demand()).set_index('Name')
            normalizatioon_factor = data.loc[buildings]['people0'].sum()
            data_processed = data_processed.apply(
                lambda x: x / normalizatioon_factor if x.name in analysis_fields else x)

        return data_processed

    def add_fields(self, df1, df2):
        """Add the analysis fields together - use this in reduce to sum up the summable parts of the dfs"""
        df1[self.schedule_analysis_fields] = df2[self.schedule_analysis_fields] + df1[self.schedule_analysis_fields]
        return df1

    def schedule_data_aggregated(self):
        data = self._calculate_input_data_aggregated()
        data_normalized = self.normalize_data(data,
                                              self.buildings,
                                              self.schedule_analysis_fields)
        resampeled_data = self.resample_time_data(data_normalized)
        return resampeled_data

    def _calculate_input_data_aggregated(self):
        """This is the data all the solar-potential plots are based on."""
        # get extra data of weather and date
        result = functools.reduce(self.add_fields,
                                  (pd.read_csv(self.locator.get_schedule_model_file(building))
                                                     for building in self.buildings)).set_index('DATE')

        return result
