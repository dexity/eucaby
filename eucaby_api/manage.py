#!/usr/bin/env python

import flask_script
from eucaby_api import models
from eucaby_api.utils import app as eucaby_app

app = eucaby_app.create_app()
app.config.from_object('eucaby_api.config.Development')

manager = flask_script.Manager(app)


@manager.command
def init_db():
    app.db.create_all()
    models.db.session.close()


if __name__ == "__main__":
    manager.run()
