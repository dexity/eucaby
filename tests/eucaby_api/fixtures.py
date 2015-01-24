import mock
from eucaby_api import models

UUID = '1z2x3c'
UUID2 = '123qweasd'
USERNAME = '12345'
LATLNG = '37.422,-122.084058'  # Google
TOKEN_TYPE = 'Bearer'
FB_PROFILE = dict(
    first_name='Test', last_name='User', verified=True,
    name='Test User', locale='en_US', gender='male',
    email='test@example.com', id=USERNAME,
    link='https://www.facebook.com/app_scoped_user_id/12345/',
    timezone=-8, updated_time='2014-12-06T21:31:50+0000')


def create_user_from_facebook(client):
    """Creates user account with Eucaby and Facebook tokens."""
    fb_valid_token = dict(access_token='someaccesstoken', expires=123)
    valid_params = dict(
        grant_type='password', service='facebook',
        password='test_password', username=USERNAME)
    with mock.patch('eucaby_api.auth.facebook.get') as fb_get:
        with mock.patch(
            'eucaby_api.auth.facebook.exchange_token') as fb_exchange_token:
            fb_exchange_token.return_value = fb_valid_token
            fb_get.return_value = mock.Mock(data=FB_PROFILE)
            client.post('/oauth/token', data=valid_params)


def create_user(user_kwargs=None, ec_token_kwargs=None,
                fb_access_token='someaccesstoken'):
    """Creates user and related tokens."""
    _user_kwargs = dict(username=USERNAME, first_name='Test', last_name='User',
                        email='test@example.com', gender='male')
    _ec_token_kwargs = dict(
        access_token=UUID, refresh_token=UUID2, expires_in=2592000,
        scope='profile history location')
    if user_kwargs:
        _user_kwargs.update(user_kwargs)
    if ec_token_kwargs:
        _ec_token_kwargs.update(ec_token_kwargs)
    user = models.User.create(**_user_kwargs)
    models.Token.create_eucaby_token(user.id, _ec_token_kwargs)
    models.Token.create_facebook_token(user.id, fb_access_token, 123)
    return user
