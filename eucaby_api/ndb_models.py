"""Datastore models for API service."""

from google.appengine.ext import ndb
from google.appengine.ext.ndb import polymodel

from eucaby_api.utils import utils as api_utils
from eucaby_api.utils import date as utils_date


class Session(ndb.Model):

    """Session model to keep track of location requests."""

    token = ndb.StringProperty(required=True, indexed=True)
    complete = ndb.BooleanProperty(default=False, indexed=True)

    @classmethod
    def create(cls):
        obj = cls(token=api_utils.generate_uuid())
        obj.put()
        return obj

    def to_dict(self):
        return self._to_dict()


class LocationMessage(polymodel.PolyModel):

    """Base model for messages."""

    uuid = ndb.StringProperty(required=True, indexed=True)
    session = ndb.StructuredProperty(Session, required=True)
    message = ndb.StringProperty()
    sender_username = ndb.StringProperty(required=True, indexed=True)
    sender_name = ndb.StringProperty()
    recipient_username = ndb.StringProperty(indexed=True)
    recipient_name = ndb.StringProperty()
    recipient_email = ndb.StringProperty(indexed=True)
    created_date = ndb.DateTimeProperty(required=True, auto_now_add=True)

    @classmethod
    def _get_by_username(cls, username_field, username, limit=None, offset=None):
        res = cls.query(getattr(cls, username_field) == username).order(
            -cls.created_date)
        kwargs = {}
        if limit is not None and offset is not None:
            kwargs = dict(limit=limit, offset=offset)
        return res.fetch(**kwargs)

    @classmethod
    def get_by_recipient_username(cls, username, limit=None, offset=None):
        """Returns messages by recipient_username."""
        return cls._get_by_username(
            'recipient_username', username, limit, offset)

    @classmethod
    def get_by_sender_username(cls, username, limit=None, offset=None):
        """Returns messages by sender_username."""
        return cls._get_by_username(
            'sender_username', username, limit, offset)

    @classmethod
    def get_by_session_token(cls, token):
        """Returns messages by session token."""
        return cls.query(
            cls.session.token == token).order(-cls.created_date).fetch()

    @classmethod
    def get_by_uuid(cls, uuid):
        """Returns message by uuid."""
        return cls.query(cls.uuid == uuid).fetch(1)

    @property
    def sender(self):
        return dict(username=self.sender_username, name=self.sender_name)

    @property
    def recipient(self):
        return dict(username=self.recipient_username, name=self.recipient_name,
                    email=self.recipient_email)

    def to_dict(self, timezone_offset=None):
        exclude = ['sender_username', 'sender_name', 'recipient_username',
                   'recipient_name', 'recipient_email']
        d = self._to_dict(exclude=exclude)
        created_date = utils_date.timezone_date(
            self.created_date, timezone_offset)
        d.update(dict(
            id=self.id, sender=self.sender, recipient=self.recipient,
            message=self.message, session=self.session.to_dict(),
            created_date=created_date))
        return d

    @property
    def id(self):
        return self.key.id()


class LocationRequest(LocationMessage):
    """Location request."""

    @classmethod
    def create(cls, sender_username, sender_name, recipient_username=None,
               recipient_name=None, recipient_email=None, message=None,
               session=None):
        """Create LocationRequest entity."""
        assert (recipient_username or recipient_email,  # pylint: disable=assert-on-tuple
                'Either recipient username or email should be set')
        if not session:
            session = Session.create()
        obj = cls(
            session=session, message=message, sender_username=sender_username,
            sender_name=sender_name, recipient_username=recipient_username,
            recipient_name=recipient_name, recipient_email=recipient_email,
            uuid=api_utils.generate_uuid())
        obj.put()
        return obj


class LocationNotification(LocationMessage):
    """Location notification."""

    location = ndb.GeoPtProperty(required=True)
    is_web = ndb.BooleanProperty(default=False, indexed=True)

    @classmethod
    def create(cls, latlng, sender_username, sender_name,
               recipient_username=None, recipient_name=None,
               recipient_email=None, message=None, is_web=False,
               session=None):
        """Create LocationNotification entity."""
        assert (recipient_username or recipient_email,  # pylint: disable=assert-on-tuple
                'Either recipient username or email should be set')
        if not session:
            session = Session.create()
        obj = cls(
            session=session, message=message, sender_username=sender_username,
            sender_name=sender_name, recipient_username=recipient_username,
            recipient_name=recipient_name, recipient_email=recipient_email,
            location=ndb.GeoPt(latlng), is_web=is_web,
            uuid=api_utils.generate_uuid())
        obj.put()
        return obj
