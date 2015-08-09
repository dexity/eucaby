# -*- coding: utf-8 -*-

import datetime
import django
import json
import mock

from django import test
from django.contrib.auth import models as auth_models
from google.appengine.ext import testbed

from eucaby.core import models
from eucaby_api import app as eucaby_app
from eucaby_api import ndb_models

from tests.eucaby_api import fixtures
from tests.eucaby_api import base as test_base
from tests.utils import utils as test_utils

django.setup()


class TestLocationView(test.TestCase):

    """Tests LocationView class."""

    def setUp(self):
        self.client = test.Client()
        self.testbed = test_utils.create_testbed()
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
        self.api_app = eucaby_app.create_app()
        self.api_app.config.from_object(test_base.Testing)
        self.api_client = self.api_app.test_client()
        self.testbed = test_utils.create_testbed()
        self.taskq = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
        self.mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)
        self.today = datetime.datetime(2015, 6, 12)
        self.loc_req = ndb_models.LocationRequest.create(
            'testuser', u'Test Юзер', recipient_email='test2@example.com',
            message=u'Привет')
        self.user = auth_models.User.objects.create(
            username='testuser', email='test@example.com', first_name='Test',
            last_name=u'Юзер')
        self.user_settings = models.UserSettings.objects.create(
            user=self.user, settings='{"email_subscription": true}')

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

    @mock.patch('eucaby.core.views.gae_utils.send_notification')
    def test_post_new_user(self, mock_send_notif):
        """Tests post request for request view for new user."""
        resp = self.client.post(
            '/request/' + self.loc_req.uuid,
            data=dict(lat='11', lng='22', message=u'Салют'))
        self.assertEqual(200, resp.status_code)
        notif = ndb_models.LocationNotification.get_by_session_token(
            self.loc_req.session.token)[0]
        data = json.loads(resp.content)
        notif_dict = notif.to_dict()
        notif_dict['created_date'] = data['created_date']
        self.assertEqual(notif_dict, data)
        self.assertEqual(u'Салют', data['message'])

        self.assertEqual(1, mock_send_notif.call_count)
        mock_send_notif.assert_called_with(
            'testuser', 'test2@example.com', 'notification', notif.id)

        task = self.taskq.get_filtered_tasks(queue_names='mail')[0]
        test_utils.execute_queue_task(self.api_client, task)
        messages = self.mail_stub.get_sent_messages()
        test_utils.verify_email(
            messages, 1, 'test@example.com',
            [u'Салют', u'Hi, Test Юзер', 'test2@example.com sent a message',
             '.com/location/' + notif.uuid])

    @mock.patch('eucaby.core.views.gae_utils.send_notification')
    def test_post_existing_user(self, mock_send_notif):
        """Tests post request for request view for existing user."""
        # Note: Tests for new and existing user are similar so we set
        #       email_subscription to false to not notify
        self.user_settings.settings = '{"email_subscription": false}'
        self.user_settings.save()

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
        notif_dict = notif.to_dict()
        notif_dict['created_date'] = data['created_date']
        self.assertEqual(notif_dict, data)
        self.assertEqual(
            dict(username='testuser2', name='Test2 User2'), data['sender'])
        self.assertEqual(
            dict(username='testuser', email=None, name=u'Test Юзер'),
            data['recipient'])

        self.assertEqual(1, mock_send_notif.call_count)
        mock_send_notif.assert_called_with(
            'testuser', 'Test2 User2', 'notification', notif.id)

        self.assertEqual(
            0, len(self.taskq.get_filtered_tasks(queue_names='mail')))
        self.assertEqual(0, len(self.mail_stub.get_sent_messages()))
