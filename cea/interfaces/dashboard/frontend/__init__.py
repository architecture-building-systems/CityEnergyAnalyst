from flask import Blueprint

blueprint = Blueprint('frontend', __name__, url_prefix='/', static_folder="build", static_url_path="/")


@blueprint.route('/')
def frontend():
    return blueprint.send_static_file('index.html')
