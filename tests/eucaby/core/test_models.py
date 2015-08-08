# -*- coding: utf-8 -*-

"""Tests for Eucaby models."""
import mock
from django import test
from django.contrib.auth import models as auth_models

from google.appengine.api import memcache

from eucaby.core import models
from tests.utils import utils as test_utils


class TestUserSettings(test.TestCase):

    def setUp(self):
        self.testbed = test_utils.create_testbed()
        self.user = auth_models.User.objects.create(
            username='test', email='test@example.com')
        self.user_settings = models.UserSettings.objects.create(
            user=self.user, settings='{"email_subscription": true}')

    def tearDown(self):
        super(TestUserSettings, self).tearDown()
        self.testbed.deactivate()

    def test_user_param(self):
        """Tests user settings param."""
        cache_key = 'user_id::{}::settings'.format(self.user.id)
        get_func = 'eucaby.core.models.UserSettings.objects.get'
        # When UserSettings object is created settings cache is not set
        self.assertIsNone(memcache.get(cache_key))
        # If cache is not set calling user_param will also call get()
        with mock.patch(get_func) as gc_mock:
            gc_mock.return_value = mock.Mock(settings='{}')
            models.UserSettings.user_param(self.user.id, 'hello')
            self.assertTrue(gc_mock.called)
            memcache.flush_all()
        # Wrong user id
        with self.assertRaises(models.UserSettings.DoesNotExist):
            models.UserSettings.user_param(123, 'hello')
        # Non-existing key
        value = models.UserSettings.user_param(self.user.id, 'hello')
        self.assertIsNone(value)
        self.assertEqual(  # user_param sets the cache
            '{"email_subscription": true}', memcache.get(cache_key))
        # If settings cache is set it shouldn't call get()
        with mock.patch(get_func) as gc_mock:
            models.UserSettings.user_param(self.user.id, 'hello')
            self.assertFalse(gc_mock.called)
