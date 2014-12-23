
import datetime
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy_utils.types import choice
from sqlalchemy.orm import exc as sqlalchemy_exceptions

from eucaby_api.utils import utils

db = SQLAlchemy()

FACEBOOK = 'facebook'
EUCABY = 'eucaby'
TOKEN_TYPE = 'Bearer'
EUCABY_EXPIRATION_SEC = 60*60*24*30  # 30 days
EUCABY_SCOPES = ['profile', 'history', 'location']

SERVICE_TYPES = [
    (EUCABY, 'Eucaby'),
    (FACEBOOK, 'Facebook')
]


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(50))
    email = db.Column(db.String(75), nullable=False)
    is_staff = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_superuser = db.Column(db.Boolean, nullable=False, default=False)
    last_login = db.Column(
        db.DateTime, nullable=False, onupdate=datetime.datetime.now)
    date_joined = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.now)

    @classmethod
    def create(cls, **kwargs):
        user = cls(
            username=kwargs['username'],
            first_name=kwargs.get('first_name', ''),
            last_name=kwargs.get('last_name', ''),
            email=kwargs.get('email', ''),
            gender=kwargs.get('gender'))
        db.session.add(user)
        db.session.commit()
        return user


class Token(db.Model):
    """Bearer token for Facebook or Eucaby."""
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(choice.ChoiceType(SERVICE_TYPES), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User')

    access_token = db.Column(db.String(512), unique=True, nullable=False)
    refresh_token = db.Column(db.String(512))
    updated_date = db.Column(
        db.DateTime, nullable=False, onupdate=datetime.datetime.now)
    expires_date = db.Column(db.DateTime, nullable=False)
    _scopes = db.Column(db.Text)

    @classmethod
    def get_or_create(cls, service, user_id, commit=False):
        """Gets or create token by service and user_id."""
        kwargs = dict(service=service, user_id=user_id)
        is_created = False
        try:
            token = cls.query.filter(**kwargs).one()
        except sqlalchemy_exceptions.MultipleResultsFound:
            tokens = cls.query.filter(**kwargs).all()
            token = tokens[0]
            for t in tokens[1:]:  # Clean up other records
                db.session.delete(t)
                db.session.commit()
        except sqlalchemy_exceptions.NoResultFound:
            token = cls(**kwargs)
        if commit:
            db.session.add(token)
            db.session.commit()
        return token

    @classmethod
    def create_or_update(cls, service, user_id, access_token, expires_seconds):

        token = cls.get_or_create(service, user_id)
        token.access_token = access_token
        token.expires_date = (
            datetime.datetime.now() + datetime.timedelta(
                seconds=expires_seconds))
        db.session.add(token)
        db.session.commit()
        return token

    @classmethod
    def provide_facebook_token(cls, user_id, access_token, expires_seconds):
        pass

    @classmethod
    def provide_eucaby_token(cls, user_id):
        """Gets or creates eucaby token."""
        token = cls.get_or_create(EUCABY, user_id)
        token.access_token = utils.generate_uuid()
        token.refresh_token = utils.generate_uuid()
        token.expires_date = (
            datetime.datetime.now() + datetime.timedelta(
                seconds=EUCABY_EXPIRATION_SEC))
        db.session.add(token)
        db.session.commit()
        return token

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []
