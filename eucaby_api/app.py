"""Application utils."""

import flask
import flask_cors
from eucaby_api import auth
from eucaby_api import config
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


def config_app(app, gae_project_id):
    """Configure the app."""
    try:
        object_str = config.CONFIG_MAP[gae_project_id]
    except KeyError:
        object_str = config.CONFIG_MAP['default']
    app.config.from_object(object_str)

    # CORS
    if app.config.get('CORS_ENABLED', False):
        flask_cors.CORS(app, allow_headers='Content-Type,Authorization')
