import mock


def create_user_account(client):
    """Creates user account with Eucaby and Facebook tokens."""
    fb_valid_token = dict(access_token='someaccesstoken', expires=123)
    fb_profile = dict(
        first_name='Test', last_name='User', verified=True,
        name='Test User', locale='en_US', gender='male',
        email='test@example.com', id='12345',
        link='https://www.facebook.com/app_scoped_user_id/12345/',
        timezone=-8, updated_time='2014-12-06T21:31:50+0000')
    valid_params = dict(
        grant_type='password', service='facebook',
        password='test_password', username='12345')
    with mock.patch('eucaby_api.auth.facebook.get') as fb_get:
        with mock.patch(
            'eucaby_api.auth.facebook.exchange_token') as fb_exchange_token:
            fb_exchange_token.return_value = fb_valid_token
            fb_get.return_value = mock.Mock(data=fb_profile)
            client.post('/oauth/token', data=valid_params)
