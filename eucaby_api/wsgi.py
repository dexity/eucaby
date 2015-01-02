"""Application runner."""

from google.appengine.api import app_identity
from eucaby_api import config
from eucaby_api.utils import app as eucaby_app

gae_project_id = app_identity.get_application_id()
app = eucaby_app.create_app()

if gae_project_id and gae_project_id == config.Production.APP_ID:
    app.config.from_object('eucaby_api.config.Production')
else:
    app.config.from_object('eucaby_api.config.Development')
