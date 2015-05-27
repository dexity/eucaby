# -*- coding: utf-8 -*-

import unittest

from google.appengine.api import taskqueue
from google.appengine.ext import testbed
import json
import mock
import random
import urllib2

from eucaby_api import args as api_args
from eucaby_api import models

from tests.eucaby_api import fixtures
from tests.eucaby_api import base as test_base
from tests.utils import utils as test_utils


class TestGCMNotifications(test_base.TestCase):

    """Tests mobile push notifications."""
    def setUp(self):
        super(TestGCMNotifications, self).setUp()
        self.client = self.app.test_client()
        self.user = fixtures.create_user()
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_mail_stub()
        self.testbed.init_taskqueue_stub(root_path='.')
        self.taskq = self.testbed.get_stub(
            testbed.TASKQUEUE_SERVICE_NAME)
        # Create devices
        device_params = [
            ('12', api_args.ANDROID), ('23', api_args.ANDROID),
            ('34', api_args.IOS)]
        self.devices = [models.Device.get_or_create(
            self.user, *param) for param in device_params]

    def tearDown(self):
        super(TestGCMNotifications, self).tearDown()
        self.testbed.deactivate()

    def _gcm_response(self, success, failure=0, canonical_ids=0, results=[]):
        """Returns GCM response."""
        resp = dict(multicast_id=random.randrange(100), success=success,
                    failure=failure, canonical_ids=canonical_ids,
                    results=results)
        return json.dumps(resp)

    def _assert_device_data(self, expected):
        """Verifies device key and active status."""
        devices = models.Device.get_by_username(
            self.user.username, api_args.ANDROID)
        self.assertEqual(expected,
                         [(dev.device_key, dev.active) for dev in devices])

    def test_general_errors(self):
        """Tests general errors for push tasks."""
        # No parameter recipient_username
        taskqueue.add(queue_name='push', url='/tasks/push/gcm')
        tasks = self.taskq.get_filtered_tasks(queue_names='push')
        self.assertEqual(1, len(tasks))
        resp = test_utils.execute_queue_task(self.client, tasks[0])
        self.assertEqual(400, resp.status_code)
        self.assertEqual('Missing recipient_username parameter', resp.data)

        # Either user or device, or user device found
        taskqueue.add(
            queue_name='push', url='/tasks/push/gcm',
            params=dict(recipient_username='unknown'))
        tasks = self.taskq.get_filtered_tasks(queue_names='push')
        resp = test_utils.execute_queue_task(self.client, tasks[1])
        self.assertEqual(404, resp.status_code)
        self.assertEqual('User device not found', resp.data)

    @mock.patch('gcm.gcm.urllib2.urlopen')
    def test_error_code(self, urlopen_mock):
        """Tests http error codes."""
        taskqueue.add(
            queue_name='push', url='/tasks/push/gcm',
            params=dict(recipient_username=self.user.username))
        tasks = self.taskq.get_filtered_tasks(queue_names='push')
        cases = [
            (400, 'The request could not be parsed as JSON'),
            (401, 'There was an error authenticating the sender account'),
            (500, 'GCM service error: 500'),
            (503, 'GCM service is unavailable')
        ]
        for case in cases:
            urlopen_mock.side_effect = urllib2.HTTPError(
                mock.Mock(), case[0], '', mock.Mock(), mock.Mock())
            resp = test_utils.execute_queue_task(self.client, tasks[0])
            self.assertEqual(500, resp.status_code)
            self.assertEqual(case[1], resp.data)

    @mock.patch('gcm.gcm.time.sleep')
    @mock.patch('gcm.gcm.urllib2.urlopen')
    def test_error_unavailable(self, urlopen_mock, sleep_mock):  # pylint: disable=unused-argument
        """Tests Unavailable error message."""
        # Mock time.sleep function so that you don't have to wait for retries
        taskqueue.add(
            queue_name='push', url='/tasks/push/gcm',
            params=dict(recipient_username=self.user.username))
        tasks = self.taskq.get_filtered_tasks(queue_names='push')
        results = [dict(message_id='0:22'), dict(error='Unavailable')]
        gcm_resp = self._gcm_response(success=1, failure=1, results=results)
        urlopen_mock.return_value = mock.Mock(
            read=mock.Mock(return_value=gcm_resp))
        resp = test_utils.execute_queue_task(self.client, tasks[0])
        # Trick to make 2 calls instead of 7 by clearing the first successful.
        self.assertEqual(2, urlopen_mock.call_count)
        # Nothing has changed in database Unavailable error doesn't modify
        self._assert_device_data([('12', True), ('23', True)])
        self.assertEqual(200, resp.status_code)

    @mock.patch('gcm.gcm.time.sleep')
    @mock.patch('gcm.gcm.urllib2.urlopen')
    def test_invalid_registration(self, urlopen_mock, sleep_mock):  # pylint: disable=unused-argument
        """Tests InvalidRegistration error message."""
        taskqueue.add(
            queue_name='push', url='/tasks/push/gcm',
            params=dict(recipient_username=self.user.username))
        tasks = self.taskq.get_filtered_tasks(queue_names='push')
        results = [dict(message_id='0:22'), dict(error='InvalidRegistration')]
        gcm_resp = self._gcm_response(success=1, failure=1, results=results)
        urlopen_mock.return_value = mock.Mock(
            read=mock.Mock(return_value=gcm_resp))
        resp = test_utils.execute_queue_task(self.client, tasks[0])
        # Device '23' is deactivated
        self._assert_device_data([('12', True)])
        self.assertEqual(200, resp.status_code)

    @mock.patch('gcm.gcm.time.sleep')
    @mock.patch('gcm.gcm.urllib2.urlopen')
    def test_not_registered(self, urlopen_mock, sleep_mock):  # pylint: disable=unused-argument
        """Tests NotRegistered error message."""
        taskqueue.add(
            queue_name='push', url='/tasks/push/gcm',
            params=dict(recipient_username=self.user.username))
        tasks = self.taskq.get_filtered_tasks(queue_names='push')
        results = [dict(message_id='0:22', registration_id='55'),
                   dict(error='NotRegistered')]
        gcm_resp = self._gcm_response(
            success=1, failure=1, canonical_ids=1, results=results)
        urlopen_mock.return_value = mock.Mock(
            read=mock.Mock(return_value=gcm_resp))
        resp = test_utils.execute_queue_task(self.client, tasks[0])
        # Device '23' is deactivated
        self._assert_device_data([('55', True)])
        self.assertEqual(200, resp.status_code)

    @mock.patch('gcm.gcm.urllib2.urlopen')
    def test_success_all_messages(self, urlopen_mock):
        """All messages are pushed successfully."""
        taskqueue.add(
            queue_name='push', url='/tasks/push/gcm',
            params=dict(recipient_username=self.user.username))
        tasks = self.taskq.get_filtered_tasks(queue_names='push')
        results = [dict(message_id='0:22'), dict(message_id='0:33')]
        gcm_resp = self._gcm_response(success=2, results=results)
        urlopen_mock.return_value = mock.Mock(
            read=mock.Mock(return_value=gcm_resp))
        resp = test_utils.execute_queue_task(self.client, tasks[0])

        # Explore request
        req = urlopen_mock.call_args[0][0]
        self.assertEqual(1, urlopen_mock.call_count)
        self.assertEqual(
            'https://android.googleapis.com/gcm/send', req.get_full_url())
        expected_data = dict(
            data=dict(message='New incoming messages', title='Eucaby'),
            registration_ids=['12', '23'])
        self.assertEqual(expected_data, json.loads(req.data))
        self.assertEqual(['Content-type', 'Authorization'], req.headers.keys())
        self.assertEqual('application/json', req.headers['Content-type'])

        # Nothing has changed in database
        self._assert_device_data([('12', True), ('23', True)])
        self.assertEqual(200, resp.status_code)

    @mock.patch('gcm.gcm.urllib2.urlopen')
    def test_success_canonical_ids(self, urlopen_mock):
        """Response has canonical ids."""
        taskqueue.add(
            queue_name='push', url='/tasks/push/gcm',
            params=dict(recipient_username=self.user.username))
        tasks = self.taskq.get_filtered_tasks(queue_names='push')
        results = [dict(message_id='0:22'),
                   dict(message_id='0:33', registration_id='44')]
        gcm_resp = self._gcm_response(
            success=2, canonical_ids=1, results=results)
        urlopen_mock.return_value = mock.Mock(
            read=mock.Mock(return_value=gcm_resp))
        resp = test_utils.execute_queue_task(self.client, tasks[0])
        self._assert_device_data([('12', True), ('44', True)])
        self.assertEqual(200, resp.status_code)


if __name__ == '__main__':
    unittest.main()