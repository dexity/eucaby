#!/usr/bin/env python

import flask_script
from eucaby_api import models
from eucaby_api import wsgi

manager = flask_script.Manager(wsgi.app)


@manager.command
def init_db():
    wsgi.app.db.create_all()
    models.db.session.close()


if __name__ == "__main__":
    manager.run()
