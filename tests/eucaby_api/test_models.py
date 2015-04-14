# -*- coding: utf-8 -*-

import flask
import unittest
import sqlalchemy
from eucaby_api import models
from tests.eucaby_api import base as test_base
from tests.eucaby_api import fixtures
from tests.utils import utils as test_utils


class TestModels(test_base.TestCase):

    """Tests User and Token models."""
    def setUp(self):
        super(TestModels, self).setUp()
        self.user = models.User.create(
            username='2345', first_name='Test', last_name=u'Юзер',
            email='test@example.com')

    def test_create_facebook_token(self):
        """Tests create facebook token."""
        params = dict(user_id=self.user.id, access_token='123qweasd',
                      expires_seconds=5)
        token = models.Token.create_facebook_token(**params)
        test_utils.assert_object(
            token, user_id=self.user.id, service=models.FACEBOOK,
            access_token=params['access_token'], refresh_token=None)
        self.assertEqual(1, models.Token.query.count())

    def test_create_or_update_eucaby_token(self):
        """Tests create and update eucaby token."""
        token_dict = dict(
            access_token=fixtures.UUID,
            expires_in=self.app.config['OAUTH2_PROVIDER_TOKEN_EXPIRES_IN'],
            refresh_token=fixtures.UUID, scope=' '.join(models.EUCABY_SCOPES),
            token_type=fixtures.TOKEN_TYPE)
        token = models.Token.create_eucaby_token(self.user.id, token_dict)
        test_utils.assert_object(
            token, user_id=self.user.id, service=models.EUCABY,
            access_token=fixtures.UUID, refresh_token=fixtures.UUID)
        self.assertEqual(1, models.Token.query.count())

        token_dict['access_token'] = fixtures.UUID2
        # Refresh token exists
        token.update_token(token_dict)
        test_utils.assert_object(
            token, user_id=self.user.id, service=models.EUCABY,
            access_token=fixtures.UUID2, refresh_token=fixtures.UUID)


class TestUserSettings(test_base.TestCase):

    """Tests UserSettings model."""
    def setUp(self):
        super(TestUserSettings, self).setUp()
        self.user = models.User.create(
            username='2345', first_name='Test', last_name=u'Юзер',
            email='test@example.com')

    def test_user_settings(self):
        """Tests that user settings are created when user is created."""
        objs = models.UserSettings.query.all()
        self.assertEqual(1, len(objs))
        # Initial settings
        self.assertEqual(flask.json.dumps(models.UserSettings.DEFAULT_SETTINGS),
                         objs[0].settings)

    def test_get_or_create(self):
        """Tests get or create method."""
        models.UserSettings.query.delete()  # Clear user settings first

        # User exists
        models.UserSettings.get_or_create(self.user.id)
        objs = models.UserSettings.query.all()
        self.assertEqual([], objs)  # Without commit set no object is created
        # User doesn't exist
        self.assertRaises(sqlalchemy.exc.IntegrityError,
                          models.UserSettings.get_or_create, (123), commit=True)
        models.db.session.rollback()    # Rollback session
        # Successful user settings creation (operation is idempotent)
        for i in range(2):  # pylint: disable=unused-variable
            obj = models.UserSettings.get_or_create(self.user.id, commit=True)
            objs = models.UserSettings.query.all()
            default_settings = flask.json.dumps(
                models.UserSettings.DEFAULT_SETTINGS)
            self.assertEqual([obj], objs)
            self.assertEqual(default_settings, obj.settings)
            self.assertEqual(
                models.UserSettings.DEFAULT_SETTINGS, obj.to_dict())

    def test_update(self):
        """Tests settings update."""
        obj = models.UserSettings.get_or_create(self.user.id)
        obj.update({}, commit=True)  # Empty settings first
        # Test A: Set settings
        obj.update(dict(hello='world'))
        self.assertEqual('{"hello": "world"}', obj.settings)
        # Settings is committed
        obj2 = models.UserSettings.query.first()
        self.assertEqual('{"hello": "world"}', obj2.settings)

        # Test B: Update settings param
        obj = models.UserSettings.get_or_create(self.user.id)
        obj.update(dict(hello='you'))
        self.assertEqual('{"hello": "you"}', obj.settings)

        # Test C: Add a new param
        obj = models.UserSettings.get_or_create(self.user.id)
        obj.update(dict(test='me'))
        self.assertEqual('{"hello": "you", "test": "me"}', obj.settings)

        # Test D: Update settings to default values
        obj = models.UserSettings.get_or_create(self.user.id)
        obj.update(None)
        obj2 = models.UserSettings.query.first()
        self.assertEqual(flask.json.dumps(models.UserSettings.DEFAULT_SETTINGS),
                         obj2.settings)

    def test_set_settings(self):
        """Tests set settings."""
        obj = models.UserSettings.get_or_create(self.user.id)
        # Empty string is not a valid json format: obj.settings = ''
        self.assertRaises(ValueError, setattr, obj, 'settings', '')
        # Valid json format
        obj.settings = '{"hello": "world"}'
        # None is allowed
        obj.settings = None
        # Empty list if also allowed
        obj.setting = '[]'

    def test_param(self):
        """Tests param method."""
        obj = models.UserSettings.get_or_create(self.user.id, commit=True)
        # No parameter set
        self.assertEqual(None, obj.param('hello'))
        # Set parameter
        obj.update({'hello': 'world'}, commit=True)
        obj2 = models.UserSettings.query.first()
        self.assertEqual('world', obj2.param('hello'))

        # Clear parameters
        obj = models.UserSettings.get_or_create(self.user.id)
        obj.update(None)
        obj2 = models.UserSettings.query.first()
        self.assertEqual(None, obj2.param('hello'))


if __name__ == '__main__':
    unittest.main()
