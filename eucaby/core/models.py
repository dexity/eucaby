from django.db import models
from google.appengine.ext import ndb

# Temp models

class Session(ndb.Model):
    key = ndb.StringProperty(required=True)
    sender_email = ndb.EmailProperty(required=True)
    receiver_email = ndb.EmailProperty(required=True)


class Request(ndb.Model):
    key = ndb.StringProperty(required=True)
    session = ndb.StructuredProperty(Session)
    created_date = ndb.DateTimeProperty(required=True)


class Response(ndb.Model):
    location = ndb.GeoPtProperty(required=True)
    session = ndb.StructuredProperty(Session)
    created_date = ndb.DateTimeProperty(required=True)
