
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
label = 'ptc_plots'

#Part II. refactor the name of this Class
class PTC_PlotBase(cea.plots.PlotBase):

    #Part III. Define category name
    #Example
    category_name = "ptc-plots"

    #Part IV. Define what parameters to show in the dashboard
    #Example:
    expected_parameters = {
        'scenario-name': 'general:scenario-name',
        'timeframe': 'plots:timeframe',
        'normalization': 'plots-ptc:normalization',   #check this with default.config
    }

    # Part V. Define what are the local inputs of the plots (files as well as variables)
    # just need to follow this format since we are working a superclass
    # Example:
    def __init__(self, project, parameters, cache):
        super(PTC_PlotBase, self).__init__(project, parameters, cache)
        self.category_path = os.path.join('new_basic', "PTC")
        self.normalization = self.parameters['normalization']
        self.input_files = self.locator.get_ptc_total_file_path()
        self.weather = self.locator.get_weather_file() #extracting time stamp from this file
        self.schedule_analysis_fields = ["Q_ptc_kwhtotal"]


    #Part VI. Define functions that can help to clean the data, normalize it etc. before it goes in the right format for plotting.
    def normalize_data(self, data_processed, analysis_fields):
        if self.normalization == "PTC area":
            data = pd.read_csv(self.locator.PVT_totals())
            normalizatioon_factor = data ["Area_PVT_m2"].values
            data_processed = data_processed.apply(
                lambda x: x / normalizatioon_factor if x.name in analysis_fields else x)
        elif self.normalization == "PVT roof area":
            data = pd.read_csv(self.locator.PVT_totals())
            normalizatioon_factor = data["PVT_roofs_top_m2"].values
            data_processed = data_processed.apply(
                lambda x: x / normalizatioon_factor if x.name in analysis_fields else x)
        return data_processed

    def add_fields(self, df1, df2):
        """Add the analysis fields together - use this in reduce to sum up the summable parts of the dfs"""
        df1[self.schedule_analysis_fields] = df2[self.schedule_analysis_fields] + df1[self.schedule_analysis_fields]
        return df1

    def schedule_data_aggregated(self):
        data = pd.read_csv(self.input_files)

        data_normalized = self.normalize_data(data,
                                              self.schedule_analysis_fields)
        resampeled_data = self.resample_time_data(data_normalized)
        return resampeled_data

