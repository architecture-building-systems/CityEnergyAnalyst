from flask import Flask
from flask_restplus import Api
from api import blueprint as api_blueprint

app = Flask(__name__)
app.register_blueprint(api_blueprint)


@app.route('/')
def index():
    return 'Hello world'


if __name__ == '__main__':
    app.run(debug=True)
