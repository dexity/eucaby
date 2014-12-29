"""Application runner."""

import flask
import os
from eucaby_api import auth
from eucaby_api import models
from eucaby_api import views


def create_app():
    """Creates Flask app."""
    fapp = flask.Flask(__name__)
    fapp.register_blueprint(views.api_app)
    auth.oauth.init_app(fapp)
    models.db.init_app(fapp)
    fapp.db = models.db
    return fapp


if __name__ == '__main__':
    app = create_app()
    if os.getenv('FLASK_CONF') == 'DEV':
        app.config.from_object('eucaby_api.config.Development')
    else:
        app.config.from_object('eucaby_api.config.Production')



