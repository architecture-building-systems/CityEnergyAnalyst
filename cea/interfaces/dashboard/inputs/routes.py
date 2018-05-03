from flask import Blueprint, render_template, redirect, url_for, current_app, request, abort, make_response

import cea.inputlocator
import os

import importlib
import plotly.offline
import json

blueprint = Blueprint(
    'inputs_blueprint',
    __name__,
    url_prefix='/inputs',
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/zone')
def zone():
    return render_template('table.html', table_name='zone')