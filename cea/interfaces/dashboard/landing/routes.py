from flask import Blueprint, render_template, redirect, request, url_for

blueprint = Blueprint(
    'landing_blueprint',
    __name__,
    url_prefix='/landing',
    template_folder='templates',
    static_folder='static'
)


@blueprint.route('/welcome')
def index():
    return render_template('landing.html')


@blueprint.route('/landing/create/<name>', methods=['POST'])
def route_create_project(name):

    return None
