# -*- coding: utf-8 -*-

import os
import datetime
import json
from eucaby.settings import utils as set_utils
os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE', set_utils.get_settings_module('testing'))

import django
from django import test
from eucaby_api import ndb_models
from google.appengine.ext import testbed
from tests.eucaby_api import fixtures

django.setup()


class TestLocationView(test.TestCase):

    """Tests LocationView class."""

    def setUp(self):
        self.client = test.Client()
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_mail_stub()
        self.today = datetime.datetime(2015, 6, 12)
        self.loc_notif = ndb_models.LocationNotification.create(
            fixtures.LATLNG, 'testuser', u'Test Юзер',
            recipient_email='test@example.com', message=u'Привет')

    def tearDown(self):
        self.testbed.deactivate()

    def test_errors(self):
        """Tests location view errors."""
        # Invalid token size
        resp = self.client.get('/location/123')
        self.assertEqual(404, resp.status_code)

        # No session
        resp = self.client.get('/location/d2a31299c6174f63a863c426a8d189cc')
        self.assertEqual(404, resp.status_code)

        # Session is expired
        self.loc_notif.created_date = self.today - datetime.timedelta(days=2)
        self.loc_notif.put()
        resp = self.client.get('/location/' + self.loc_notif.uuid)
        self.assertEqual(200, resp.status_code)
        self.assertIn('Location link has expired', resp.content)

    def test_get(self):
        """Tests get request for location view."""
        resp = self.client.get('/location/' + self.loc_notif.uuid)
        content = resp.content.decode('utf-8')
        self.assertEqual(200, resp.status_code)
        self.assertIn('LocationCtrl', content)
        self.assertIn(u'Test Юзер', content)
        self.assertIn(u'Привет', content)


class TestNotifyLocationView(test.TestCase):

    """Tests NotifyLocationView class."""

    def setUp(self):
        self.client = test.Client()
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_mail_stub()
        self.today = datetime.datetime(2015, 6, 12)
        self.loc_req = ndb_models.LocationRequest.create(
            'testuser', u'Test Юзер', recipient_email='test@example.com',
            message=u'Привет')

    def tearDown(self):
        self.testbed.deactivate()

    def test_errors(self):
        """Tests request view errors."""
        # Invalid token size
        resp = self.client.get('/request/123')
        self.assertEqual(404, resp.status_code)

        resp = self.client.post('/request/123')
        self.assertEqual(404, resp.status_code)

        # No session
        resp = self.client.get('/location/d2a31299c6174f63a863c426a8d189cc')
        self.assertEqual(404, resp.status_code)

        resp = self.client.post('/request/d2a31299c6174f63a863c426a8d189cc')
        self.assertEqual(404, resp.status_code)

        # Session is expired
        self.loc_req.created_date = self.today - datetime.timedelta(days=2)
        self.loc_req.put()
        resp = self.client.get('/request/' + self.loc_req.uuid)
        self.assertEqual(200, resp.status_code)
        self.assertIn('Request link has expired', resp.content)

        resp = self.client.post('/request/' + self.loc_req.uuid)
        self.assertEqual(200, resp.status_code)
        self.assertIn('Request link has expired', resp.content)

    def test_post_errors(self):
        """Tests request view errors specific to post request."""
        # Invalid location
        invalid_location = dict(error='Invalid location')
        params = [{}, dict(lat='a', lng='b'), dict(lat='11'), dict(lng='22')]
        for param in params:
            resp = self.client.post('/request/' + self.loc_req.uuid, data=param)
            self.assertEqual(400, resp.status_code)
            self.assertEqual(invalid_location, json.loads(resp.content))

        # Invalid message
        invalid_message = dict(error='Message exceeds 1000 characters')
        resp = self.client.post(
            '/request/' + self.loc_req.uuid,
            data=dict(lat='11', lng='22', message='a'*1100))
        self.assertEqual(400, resp.status_code)
        self.assertEqual(invalid_message, json.loads(resp.content))

    def test_get(self):
        """Tests get request for request view."""
        resp = self.client.get('/request/' + self.loc_req.uuid)
        content = resp.content.decode('utf-8')
        self.assertEqual(200, resp.status_code)
        self.assertIn('RequestCtrl', content)
        self.assertIn(u'Test Юзер', content)

    def test_post(self):
        """Tests post request for request view."""
        # Non-existing user
        resp = self.client.post(
            '/request/' + self.loc_req.uuid,
            data=dict(lat='11', lng='22', message=u'Салют'))
        self.assertEqual(200, resp.status_code)
        notif = ndb_models.LocationNotification.get_by_session_token(
            self.loc_req.session.token)[0]
        data = json.loads(resp.content)
        self.assertEqual(notif.to_dict(), data)
        self.assertEqual(u'Салют', data['message'])

        # Existing user
        loc_req2 = ndb_models.LocationRequest.create(
            'testuser', u'Test Юзер', recipient_username='testuser2',
            recipient_name='Test2 User2', message=u'Привет')

        resp = self.client.post(
            '/request/' + loc_req2.uuid,
            data=dict(lat='11', lng='22', message=u'Салют'))
        self.assertEqual(200, resp.status_code)
        notif = ndb_models.LocationNotification.get_by_session_token(
            loc_req2.session.token)[0]
        data = json.loads(resp.content)
        self.assertEqual(notif.to_dict(), data)
        self.assertEqual(
            dict(username='testuser2', name='Test2 User2'), data['sender'])
        self.assertEqual(
            dict(username='testuser', email=None, name=u'Test Юзер'),
            data['recipient'])
