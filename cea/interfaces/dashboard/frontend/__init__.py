import os.path
from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile

from flask import Blueprint

blueprint = Blueprint('frontend', __name__, url_prefix='/', static_folder="build", static_url_path="/")


@blueprint.route('/')
def frontend():
    return blueprint.send_static_file('index.html')


def get_build():
    url = "https://github.com/architecture-building-systems/CityEnergyAnalyst-GUI/releases/download/v3.32.0-browser/build.zip"
    output = os.path.dirname(os.path.abspath(__file__))

    if os.path.exists(os.path.join(output, "build")):
        return

    with urlopen(url) as r:
        with ZipFile(BytesIO(r.read())) as f:
            f.extractall(output)


get_build()
