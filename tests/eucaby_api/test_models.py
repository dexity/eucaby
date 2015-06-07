# -*- coding: utf-8 -*-

import flask
import unittest
import sqlalchemy
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


class TestDevice(test_base.TestCase):

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
        self.devices = [models.Device.get_or_create(
            self.user, *param) for param in device_params]
        self.devices[0].deactivate()

        def _verify_devices(username, devices):
            objs = models.Device.get_by_username(username)
            self.assertEqual(devices, objs)

        # No device keys or no devices for the device keys
        cases = [[], ['11', '22']]
        for device_keys in cases:
            models.Device.deactivate_multiple(device_keys)
            _verify_devices(self.user.username, self.devices[1:])

        # Existing devices
        models.Device.deactivate_multiple(['23', '34'])
        _verify_devices(self.user.username, self.devices[3:])

        # Deactivate by platform
        # Has no iOS device with the device_key
        models.Device.deactivate_multiple(['45',], platform=api_args.IOS)
        _verify_devices(self.user.username, self.devices[3:])

        # Has Android device with the device_key
        models.Device.deactivate_multiple(['45',], platform=api_args.ANDROID)
        _verify_devices(self.user.username, [])


if __name__ == '__main__':
    unittest.main()
