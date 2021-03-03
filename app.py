from my_flask import FlaskAPP
from werkzeug.serving import run_simple

app = FlaskAPP(__name__)


@app.route('/index', methods=['GET'])
def index():
    return "haha"''


@app.error_handler(404)
def error404():
    return "傻逼"


@app.before_request
def a():
    return 'haha'


if __name__ == '__main__':
    run_simple('127.0.0.1', 5000, app)