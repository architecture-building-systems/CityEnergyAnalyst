from flask import Blueprint, render_template

blueprint = Blueprint(
    'home_blueprint',
    __name__,
    url_prefix='/home',
    template_folder='templates',
    static_folder='static'
)


@blueprint.route('/index')
def index():
    return render_template('index.html')


@blueprint.route('/<template>')
def route_template(template):
    return render_template(template + '.html')
