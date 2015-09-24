# -*- coding: utf-8 -*-
"""Tests for Eucaby API models."""

import flask
import mock
import unittest

from google.appengine.api import memcache
from sqlalchemy.orm import exc as orm_exc

from eucaby_api import args as api_args
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
        token_obj = models.Token.query.first()  # Query form database
        test_utils.assert_object(
            token_obj, user_id=self.user.id, service=models.EUCABY,
            access_token=fixtures.UUID2, refresh_token=fixtures.UUID)


class TestUserSettings(test_base.TestCase):

    """Tests UserSettings model."""
    def setUp(self):
        super(TestUserSettings, self).setUp()
        self.testbed = test_utils.create_testbed()
        self.user = models.User.create(
            username='2345', first_name='Test', last_name=u'Юзер',
            email='test@example.com')

    def tearDown(self):
        super(TestUserSettings, self).tearDown()
        self.testbed.deactivate()

    def test_user_settings(self):
        """Tests that user settings are created when user is created."""
        objs = models.UserSettings.query.all()
        self.assertEqual(1, len(objs))
        # Initial settings
        self.assertEqual(flask.json.dumps(models.UserSettings.DEFAULT_SETTINGS),
                         objs[0].settings)

    def test_get_or_create(self):
        """Tests get or create user settings."""
        models.UserSettings.query.delete()  # Clear user settings first

        # User exists
        models.UserSettings.get_or_create(self.user.id, commit=False)
        objs = models.UserSettings.query.all()
        # With commit set to False no object is created
        self.assertEqual([], objs)
        # User doesn't exist
        self.assertRaises(orm_exc.NoResultFound,
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

    @unittest.skip('Skip restricting setting the settings field')
    def test_set_settings(self):
        """Tests set settings."""
        obj = models.UserSettings.get_or_create(self.user.id)
        # Empty string is not a valid json format: obj.settings = ''
        self.assertRaises(ValueError, setattr, obj, 'settings', '')
        obj.settings = '{"hello": "world"}'  # Valid json format
        obj.settings = None  # None is allowed
        obj.setting = '[]'  # Empty list if also allowed

    def test_param(self):
        """Tests param method."""
        obj = models.UserSettings.get_or_create(self.user.id, commit=True)
        self.assertEqual(None, obj.param('hello'))  # No parameter set
        obj.update({'hello': 'world'}, commit=True)  # Set parameter
        obj2 = models.UserSettings.query.first()
        self.assertEqual('world', obj2.param('hello'))

        # Clear parameters
        obj = models.UserSettings.get_or_create(self.user.id)
        obj.update(None)
        obj2 = models.UserSettings.query.first()
        self.assertEqual(None, obj2.param('hello'))

    def test_user_param(self):
        """Tests user settings param."""
        cache_key = 'user_id::{}::settings'.format(self.user.id)
        get_or_create = 'eucaby_api.models.UserSettings.get_or_create'
        # When UserSettings object is created settings cache is not set
        self.assertIsNone(memcache.get(cache_key))
        # If cache is not set calling user_param will also call get_or_create
        with mock.patch(get_or_create) as gc_mock:
            gc_mock.return_value = mock.Mock(settings='{}')
            models.UserSettings.user_param(self.user.id, 'hello')
            self.assertTrue(gc_mock.called)
            memcache.flush_all()
        # Wrong user id
        with self.assertRaises(orm_exc.NoResultFound):
            models.UserSettings.user_param('wrong', 'hello')
        # Non-existing key
        value = models.UserSettings.user_param(self.user.id, 'hello')
        self.assertIsNone(value)
        self.assertEqual(  # user_param sets the cache
            '{"email_subscription": true}', memcache.get(cache_key))
        # If settings cache is set it shouldn't call get_or_create
        with mock.patch(get_or_create) as gc_mock:
            models.UserSettings.user_param(self.user.id, 'hello')
            self.assertFalse(gc_mock.called)
        # Updating settings should refresh the cache
        obj = models.UserSettings.get_or_create(self.user.id)
        obj.update(dict(hello='world'))
        text = '{"email_subscription": true, "hello": "world"}'
        self.assertEqual(text, memcache.get(cache_key))
        value = models.UserSettings.user_param(self.user.id, 'hello')
        self.assertEqual('world', value)


class TestDevice(test_base.TestCase):

    """Tests Device model."""
    def setUp(self):
        super(TestDevice, self).setUp()
        self.user = models.User.create(
            username='2345', first_name='Test', last_name=u'Юзер',
            email='test@example.com')
        self.user2 = models.User.create(
            username='1234', first_name='Test2', last_name=u'Юзер2',
            email='test2@example.com')

    def test_create(self):
        """Create device is indempotent."""
        for i in range(2):  # pylint: disable=unused-variable
            obj = models.Device.get_or_create(
                self.user, 'somedevicekey', 'android')
            objs = models.Device.query.all()
            self.assertEqual(1, len(objs))
            self.assertEqual(objs[0], obj)
            test_utils.assert_object(
                obj, device_key='somedevicekey', platform='android')
            self.assertEqual(1, len(obj.users))

    def test_many_users(self):
        """Two and more users can be associated with the same device."""
        obj = models.Device.get_or_create(self.user, 'somedevicekey', 'android')
        obj2 = models.Device.get_or_create(
            self.user2, 'somedevicekey', 'android')
        objs = models.Device.query.all()
        self.assertEqual(1, len(objs))
        self.assertEqual(obj, obj2)
        # Should have two users
        self.assertEqual([self.user, self.user2], obj.users)

    def test_get_by_user(self):
        """List of devices by user."""
        obj1 = models.Device.get_or_create(
            self.user, 'somedevicekey', 'android')
        obj2 = models.Device.get_or_create(
            self.user, 'olddevicekey', 'ios')
        models.Device.get_or_create(
            self.user2, 'newdevicekey', 'android')
        objs = models.Device.get_by_username(self.user.username)
        self.assertEqual([obj1, obj2], objs)
        # Filter by platform
        objs = models.Device.get_by_username(
            self.user.username, platform='android')
        self.assertEqual([obj1], objs)
        # Deactivate one device
        obj2.deactivate()
        self.assertFalse(obj2.active)
        self.assertEqual(
            [obj1], models.Device.get_by_username(self.user.username))

    def test_deactivate_multiple(self):
        """Tests deactivate multiple devices."""
        # Create devices
        device_params = [
            ('12', api_args.ANDROID), ('23', api_args.IOS),
            ('34', api_args.IOS), ('45', api_args.ANDROID)]
        devices = [models.Device.get_or_create(
            self.user, *param) for param in device_params]
        devices[0].deactivate()

        def _verify_devices(username, device_objs):
            objs = models.Device.get_by_username(username)
            self.assertEqual(device_objs, objs)

        # No device keys or no devices for the device keys
        cases = [[], ['11', '22']]
        for device_keys in cases:
            models.Device.deactivate_multiple(device_keys)
            _verify_devices(self.user.username, devices[1:])

        # Existing devices
        models.Device.deactivate_multiple(['23', '34'])
        _verify_devices(self.user.username, devices[3:])

        # Deactivate by platform
        # Has no iOS device with the device_key
        models.Device.deactivate_multiple(['45',], platform=api_args.IOS)
        _verify_devices(self.user.username, devices[3:])

        # Has Android device with the device_key
        models.Device.deactivate_multiple(['45',], platform=api_args.ANDROID)
        _verify_devices(self.user.username, [])


class TestEmailHistory(test_base.TestCase):

    """Tests EmailHistory model."""
    def setUp(self):
        super(TestEmailHistory, self).setUp()
        self.user = models.User.create(
            username='2345', first_name='Test', last_name=u'Юзер',
            email='test@example.com')
        self.user2 = models.User.create(
            username='1234', first_name='Test2', last_name=u'Юзер2',
            email='test2@example.com')

    def test_get_or_create(self):
        """Tests get or create email history."""
        cases = ['hello', 'Hello']
        for text in cases:
            obj = models.EmailHistory.get_or_create(self.user.id, text)
            self.assertEqual('hello', obj.text)
        self.assertEqual(1, models.EmailHistory.query.count())

    def test_get_by_user(self):
        """Tests filtering by user."""
        # Populate email history
        cases = (
            (self.user, ['Alaska', 'Arkansas', 'arizona', 'ARIZONA', 'colorado',
                         'Connecticut', 'California']),
            (self.user2, ['alabama', ]))
        for user, text_list in cases:
            for text in text_list:
                models.EmailHistory.get_or_create(user.id, text=text)

        all_list = ['alaska', 'arizona', 'arkansas', 'california', 'colorado',
                    'connecticut']
        cases = (
            (dict(user_id=None), []),  # Unknow user
            (dict(user_id=self.user.id), all_list),  # Get by user
            # Empty query
            (dict(user_id=self.user.id, query=''), []),
            # Query with empty result
            (dict(user_id=self.user.id, query='d'), []),
            # Query with result, no limit
            (dict(user_id=self.user.id, query='ar'), ['arizona', 'arkansas']),
            # Query with limit
            (dict(user_id=self.user.id, query='a', limit=2),
             ['alaska', 'arizona']),
            # Query with large limit
            (dict(user_id=self.user.id, query='a', limit=100),
             ['alaska', 'arizona', 'arkansas']))
        for kwargs, email_list in cases:
            objs = models.EmailHistory.get_by_user(**kwargs)
            self.assertEqual(email_list, [obj.text for obj in objs])


if __name__ == '__main__':
    unittest.main()
