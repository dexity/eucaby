
import flask
import os
from eucaby_api import views
from eucaby_api import auth
from eucaby_api import models

def create_app():
    app = flask.Flask(__name__)
    app.register_blueprint(views.api_app)
    auth.oauth.init_app(app)
    models.db.init_app(app)
    app.db = models.db
    return app

if __name__ == '__main__':
    app = create_app()
    if os.getenv('FLASK_CONF') == 'DEV':
        app.config.from_object('eucaby_api.config.Development')
    else:
        app.config.from_object('eucaby_api.config.Production')



