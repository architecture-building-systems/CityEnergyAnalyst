from flask import Blueprint, render_template, redirect, request, url_for

# start the login system

blueprint = Blueprint(
    'landing_blueprint',
    __name__,
    url_prefix='',
    template_folder='templates',
    static_folder='static'
)


@blueprint.route('/index')
def index():
    return redirect(url_for('landing_blueprint.route_landing'))


@blueprint.route('/landing')
def route_landing():

    return render_template('landing.html')


@blueprint.route('/landing/create/<name>', methods=['POST'])
def route_create_project(name):

    return
