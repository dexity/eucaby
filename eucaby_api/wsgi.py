"""Application runner."""

import os
from eucaby_api.utils import app as eucaby_app

app = eucaby_app.create_app()
if os.getenv('FLASK_CONF') == 'DEV':
    app.config.from_object('eucaby_api.config.Development')
else:
    app.config.from_object('eucaby_api.config.Production')
