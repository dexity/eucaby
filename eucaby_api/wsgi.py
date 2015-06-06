"""Application runner."""

from google.appengine.api import app_identity
from eucaby_api import app as eucaby_app

gae_project_id = app_identity.get_application_id()
app = eucaby_app.create_app()
eucaby_app.config_app(app, gae_project_id)
