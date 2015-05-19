"""Application utils."""

import flask
from eucaby_api import auth
from eucaby_api import models
from eucaby_api import views
from eucaby_api import tasks


def create_app():
    """Creates Flask app."""
    _app = flask.Flask(__name__)
    _app.register_blueprint(views.api_app)
    _app.register_blueprint(tasks.tasks_app, url_prefix='/tasks')
    auth.oauth.init_app(_app)
    auth.eucaby_oauth.init_app(_app)
    models.db.init_app(_app)
    _app.db = models.db
    return _app
