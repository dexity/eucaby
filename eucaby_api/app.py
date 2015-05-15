"""Application utils."""

import flask
from eucaby_api import auth
from eucaby_api import models
from eucaby_api import views
from eucaby_api import tasks


def create_app():
    """Creates Flask app."""
    fapp = flask.Flask(__name__)
    fapp.register_blueprint(views.api_app)
    fapp.register_blueprint(tasks.tasks_app, url_prefix='/tasks')
    auth.oauth.init_app(fapp)
    auth.eucaby_oauth.init_app(fapp)
    models.db.init_app(fapp)
    fapp.db = models.db
    return fapp
