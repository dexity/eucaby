
Eucaby
======

Application for real-time location discovery

Install application
-------------------

```
$ ./install.sh
```

Eucaby API
==========

Create Database
---------------

Local Development environment:

```
$ FLASK_CONF=DEV ./eucaby_api/manage.py init_db
```

Project `eucaby-dev`:

```
$ FLASK_CONF=REMOTE_DEV ./eucaby_api/manage.py init_db
```

Project `eucaby-prd`:

```
$ FLASK_CONF=REMOTE_PRD ./eucaby_api/manage.py init_db
```
