#!/usr/bin/env python

import flask_script
import os
from eucaby_api import models
from eucaby_api import app as eucaby_app

env = os.environ.get('FLASK_CONF', 'DEV')
app = eucaby_app.create_app()

if env == 'REMOTE_PRD':
    app.config.from_object('eucaby_api.config.RemoteProduction')
elif env == 'REMOTE_DEV':
    app.config.from_object('eucaby_api.config.RemoteDevelopment')
else:
    app.config.from_object('eucaby_api.config.LocalDevelopment')

manager = flask_script.Manager(app)


@manager.command
def init_db():
    app.db.create_all()
    models.db.session.close()


if __name__ == "__main__":
    manager.run()
