"""SQL models for API service."""

import datetime
import flask_sqlalchemy
from sqlalchemy_utils.types import choice

db = flask_sqlalchemy.SQLAlchemy()

FACEBOOK = 'facebook'
EUCABY = 'eucaby'
EUCABY_SCOPES = ['profile', 'history', 'location']

SERVICE_TYPES = [
    (EUCABY, 'Eucaby'),
    (FACEBOOK, 'Facebook')
]


class User(db.Model):

    """User model.

    Notes:
        email can be empty because Facebook user might be authenticated with
        the phone number. "This field will not be returned if no valid email
        address is available."
        See: https://developers.facebook.com/docs/graph-api/reference/v2.2/user
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(50))
    email = db.Column(db.String(75))
    is_staff = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_superuser = db.Column(db.Boolean, nullable=False, default=False)
    last_login = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.now,
        onupdate=datetime.datetime.now)
    date_joined = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.now)

    @classmethod
    def create(cls, **kwargs):
        """Creates user."""
        user = cls(
            username=kwargs['username'],
            first_name=kwargs.get('first_name', ''),
            last_name=kwargs.get('last_name', ''),
            email=kwargs.get('email', ''),
            gender=kwargs.get('gender'))
        db.session.add(user)
        db.session.commit()
        return user

    @property
    def name(self):
        return '{} {}'.format(self.first_name, self.last_name)


class Token(db.Model):

    """Bearer token for Facebook or Eucaby."""

    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(choice.ChoiceType(SERVICE_TYPES), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User')

    access_token = db.Column(db.String(255), unique=True, nullable=False)
    refresh_token = db.Column(db.String(255), unique=True)
    created_date = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.now)
    updated_date = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.now,
        onupdate=datetime.datetime.now)
    expires = db.Column(db.DateTime, nullable=False)
    scope = db.Column(db.Text)

    @classmethod
    def create_facebook_token(cls, user_id, access_token, expires_seconds):
        """Creates Facebook token."""
        # Note: It doesn't create user
        token = cls(
            service=FACEBOOK, user_id=user_id, access_token=access_token,
            expires=datetime.datetime.now() + datetime.timedelta(
                seconds=expires_seconds))
        db.session.add(token)
        db.session.commit()
        return token

    @classmethod
    def create_eucaby_token(cls, user_id, token):
        """Creates Eucaby token."""
        # Note: It doesn't create user
        token = cls(
            service=EUCABY, user_id=user_id,
            access_token=token['access_token'],
            refresh_token=token['refresh_token'],
            expires=datetime.datetime.now() + datetime.timedelta(
                seconds=token['expires_in']),
            scope=token['scope'])
        db.session.add(token)
        db.session.commit()
        return token

    def update_token(self, token):
        """Refreshes existing token. Doesn't update the refresh_token."""
        # Only Eucaby can be refreshed. Facebook has no way to do that
        self.access_token = token['access_token']
        self.expires = (datetime.datetime.now() +
                        datetime.timedelta(seconds=token['expires_in']))
        db.session.add(self)
        db.session.commit()

    @property
    def scopes(self):
        if self.scope:
            return self.scope.split()
        return []
