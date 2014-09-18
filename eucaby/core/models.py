#from django.db import models
import datetime
from google.appengine.ext import ndb
import uuid

# Temp models

class Session(ndb.Model):
    key = ndb.StringProperty(required=True)
    sender_email = ndb.StringProperty(required=True)
    receiver_email = ndb.StringProperty(required=True)

    @classmethod
    def create(cls, sender_email, receiver_email):
        obj = cls(
            key=uuid.uuid4().hex, sender_email=sender_email,
            receiver_email=receiver_email)
        obj.put()
        return obj


class Request(ndb.Model):
    token = ndb.StringProperty(required=True)
    session = ndb.StructuredProperty(Session, required=True)
    created_date = ndb.DateTimeProperty(required=True)

    @classmethod
    def create(cls, session):
        obj = cls(
            token=uuid.uuid4().hex, session=session,
            created_date=datetime.datetime.now())
        obj.put()
        return obj


class Response(ndb.Model):
    location = ndb.GeoPtProperty(required=True)
    session = ndb.StructuredProperty(Session, required=True)
    created_date = ndb.DateTimeProperty(required=True)
