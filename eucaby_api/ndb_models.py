"""Datastore models for API service."""

import datetime
from google.appengine.ext import ndb

from eucaby_api.utils import utils as api_utils


class BaseModel(ndb.Model):

    """Base model."""

    @property
    def id(self):
        return self.key.id()


class Session(BaseModel):

    """Session model to keep track location requests."""

    key = ndb.StringProperty(required=True, indexed=True)
    sender_username = ndb.StringProperty(required=True, indexed=True)
    recipient_username = ndb.StringProperty(indexed=True)
    recipient_email = ndb.StringProperty(indexed=True)
    complete = ndb.BooleanProperty(default=False, indexed=True)

    @classmethod
    def create(cls, sender_username, recipient_username=None,
               recipient_email=None):
        """Create Session entity."""
        assert (recipient_username or recipient_email,  # pylint: disable=assert-on-tuple
                'Either recipient username or email should be set')
        obj = cls(
            key=api_utils.generate_uuid(), sender_username=sender_username,
            recipient_username=recipient_username,
            recipient_email=recipient_email)
        obj.put()
        return obj

    def to_dict(self):
        return self._to_dict()


class LocationRequest(BaseModel):
    token = ndb.StringProperty(required=True, indexed=True)  # ?
    session = ndb.StructuredProperty(Session, required=True)
    created_date = ndb.DateTimeProperty(required=True)

    @classmethod
    def create(cls, session):
        obj = cls(
            token=api_utils.generate_uuid(), session=session,
            created_date=datetime.datetime.now())
        obj.put()
        return obj

    def to_dict(self):
        return dict(
            token=self.token, session=self.session.to_dict(),
            created_date=str(self.created_date))


class LocationResponse(BaseModel):
    location = ndb.GeoPtProperty(required=True)
    session = ndb.StructuredProperty(Session, required=True)
    created_date = ndb.DateTimeProperty(required=True)

    @classmethod
    def create(cls, session, latlng):
        obj = cls(
            location=ndb.GeoPt(latlng), session=session,
            created_date=datetime.datetime.now())
        obj.put()
        return obj

    def to_dict(self):
        return dict(
            location=dict(
                lat=self.location.lat, lng=self.location.lon),
            session=self.session.to_dict(),
            created_date=str(self.created_date))
