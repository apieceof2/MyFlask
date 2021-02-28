from my_flask import FlaskAPP
from werkzeug.serving import run_simple

if __name__ == '__main__':
    app = FlaskAPP(__name__)
    run_simple('127.0.0.1', 5000, app)