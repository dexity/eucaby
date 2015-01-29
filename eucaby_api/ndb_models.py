"""Datastore models for API service."""

from google.appengine.ext import ndb
from google.appengine.ext.ndb import polymodel

from eucaby_api.utils import utils as api_utils


class Session(ndb.Model):

    """Session model to keep track of location requests."""

    key = ndb.StringProperty(required=True, indexed=True)
    complete = ndb.BooleanProperty(default=False, indexed=True)

    @classmethod
    def create(cls):
        obj = cls(key=api_utils.generate_uuid())
        obj.put()
        return obj

    def to_dict(self):
        return self._to_dict()


class LocationMessage(polymodel.PolyModel):

    """Base model for messages."""

    session = ndb.StructuredProperty(Session, required=True)
    sender_username = ndb.StringProperty(required=True, indexed=True)
    recipient_username = ndb.StringProperty(indexed=True)
    recipient_email = ndb.StringProperty(indexed=True)
    created_date = ndb.DateTimeProperty(required=True, auto_now_add=True)

    def to_dict(self):
        return dict(
            session=self.session.to_dict(),
            sender_username=self.sender_username,
            recipient_username=self.recipient_username,
            recipient_email=self.recipient_email,
            created_date=str(self.created_date))

    @property
    def id(self):
        return self.key.id()


class LocationRequest(LocationMessage):
    """Location request."""

    @classmethod
    def create(cls, sender_username, recipient_username=None,
               recipient_email=None, session=None):
        """Create LocationRequest entity."""
        assert (recipient_username or recipient_email,  # pylint: disable=assert-on-tuple
                'Either recipient username or email should be set')
        if not session:
            session = Session.create()
        obj = cls(
            session=session, sender_username=sender_username,
            recipient_username=recipient_username,
            recipient_email=recipient_email)
        obj.put()
        return obj

class LocationNotification(LocationMessage):
    """Location notification."""

    location = ndb.GeoPtProperty(required=True)

    @classmethod
    def create(cls, latlng, sender_username, recipient_username=None,
               recipient_email=None, session=None):
        """Create LocationNotification entity."""
        assert (recipient_username or recipient_email,  # pylint: disable=assert-on-tuple
                'Either recipient username or email should be set')
        if not session:
            session = Session.create()
        obj = cls(
            session=session, sender_username=sender_username,
            recipient_username=recipient_username,
            recipient_email=recipient_email, location = ndb.GeoPt(latlng))
        obj.put()
        return obj

    def to_dict(self):
        res = super(LocationNotification, self).to_dict()
        res['location'] = dict(
            lat=self.location.lat, lng=self.location.lon)
        return res
