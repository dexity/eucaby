
import flask

app = flask.Flask(__name__)

@app.route('/')
def test():
    return 'Hello'


