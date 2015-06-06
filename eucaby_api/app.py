"""Application utils."""

import apns
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


def set_apns_socket(app):
    """Creates APNs socket. App should be configured"""
    app.apns_socket = apns.APNs(
        use_sandbox=app.config['APNS_USE_SANDBOX'],
        cert_file=app.config['APNS_CERT_FILE'],
        key_file=app.config['APNS_KEY_FILE'],
        enhanced=True)


def config_app(app, gae_project_id):
    """Configure the app."""
    if gae_project_id and gae_project_id == config.Production.APP_ID:
        app.config.from_object('eucaby_api.config.Production')
    elif gae_project_id and gae_project_id == config.Development.APP_ID:
        app.config.from_object('eucaby_api.config.Development')
    else:
        app.config.from_object('eucaby_api.config.LocalDevelopment')

    set_apns_socket(app)

    # CORS
    if app.config.get('CORS_ENABLED', False):
        flask_cors.CORS(app, allow_headers='Content-Type,Authorization')
