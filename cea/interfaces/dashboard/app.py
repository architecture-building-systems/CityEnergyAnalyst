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
    return render_template('dashboard.html', load_curve_div=r'<div>hello, load_curve_div</div>',
                           plots=cea.interfaces.dashboard.plots.list_plots())

@app.route('/plot/<plot_name>/<building>', methods=['GET'])
def plot(plot_name, building):
    plot = cea.interfaces.dashboard.plots.get_plot(plot_name)

    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)

    # GET TIMESERIES DATA
    df = pd.read_csv(locator.get_demand_results_file(building)).set_index("DATE")

    # GET LOCAL WEATHER CONDITIONS
    weather_data = cea.utilities.epwreader.epw_reader(config.weather)[["drybulb_C", "wetbulb_C", "skytemp_C"]]
    df["T_out_dry_C"] = weather_data["drybulb_C"].values
    df["T_out_wet_C"] = weather_data["wetbulb_C"].values
    df["T_sky_C"] = weather_data["skytemp_C"].values

    # CREATE LOAD CURVE
    title = "Load Curve for Building " + building
    analysis_fields = ["Ef_kWh", "Qhsf_kWh", "Qwwf_kWh", "Qcsf_kWh", "T_int_C", "T_out_dry_C"]

    return plot.producer(data_frame=df, analysis_fields=analysis_fields, title=title)



if __name__ == '__main__':
    app.run(host="localhost", port=5000, debug=True, use_reloader=True)
