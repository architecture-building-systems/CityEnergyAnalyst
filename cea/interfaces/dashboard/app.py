# -----------------------------------
#     app.py
#     version: 1.0.0
#     Author: Andrew Shay
#     Created: December 10 2015
#     Description: The Flask server that powers Neuron
# -----------------------------------

import pandas as pd

from flask import Flask
from flask import render_template
from flask import request

import cea.interfaces.dashboard.plots
import cea.config
import cea.inputlocator
import cea.utilities.epwreader

app = Flask(__name__)
files = None


@app.before_request
def before_request():
    pass


@app.teardown_request
def teardown_request(exception):
    pass


@app.route('/', methods=['GET'])
def index():
    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    return render_template('dashboard.html',
                           buildings=locator.get_zone_building_names(),
                           plots=cea.interfaces.dashboard.plots.list_plots())

@app.route('/plot/<plot_name>/<building>', methods=['GET'])
def plot(plot_name, building):
    print('plotting plot %s for building %s' % (plot_name, building))
    plot = cea.interfaces.dashboard.plots.get_plot(plot_name)

    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)

    # GET TIMESERIES DATA
    df = pd.read_csv(locator.get_demand_results_file(building)).set_index("DATE")

    # CREATE LOAD CURVE
    title = "Load Curve for Building " + building
    analysis_fields = ["Ef_kWh", "Qhsf_kWh", "Qwwf_kWh", "Qcsf_kWh", "T_int_C", "T_ext_C"]

    return plot.producer(data_frame=df, analysis_fields=analysis_fields, title=title)



if __name__ == '__main__':
    app.run(host="localhost", port=5000, debug=True, use_reloader=True)
