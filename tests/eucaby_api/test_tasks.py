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


def _gcm_response(success, failure=0, canonical_ids=0, results=None):
    """Returns GCM response."""
    resp = dict(multicast_id=random.randrange(100), success=success,
                failure=failure, canonical_ids=canonical_ids,
                results=results or [])
    return json.dumps(resp)


class TestPushNotifications(test_base.TestCase):

    def _assert_general_errors(self, url):
        kwargs = dict(queue_name='push', url=url)
        cases = (
            (None, 'Missing recipient_username parameter'),
            (dict(recipient_username=self.user.username,),
             'Message type can be either notification or request'),
            (dict(recipient_username=self.user.username, message_type='wrong'),
             'Message type can be either notification or request'),
            (dict(recipient_username=self.user.username,
                  message_type=api_args.NOTIFICATION),
             'Missing message_id parameter'),
            (dict(recipient_username='unknown',
                  message_type=api_args.NOTIFICATION, message_id=123),
             'No android devices found'))
        for i in range(len(cases)):
            case = cases[i]
            qkwargs = kwargs.copy()
            if case[0]:  # params parameter
                qkwargs['params'] = case[0]
            taskqueue.add(**qkwargs)
            tasks = self.taskq.get_filtered_tasks(queue_names='push')
            self.assertEqual(i+1, len(tasks))
            resp = test_utils.execute_queue_task(self.client, tasks[i])
            # The failed task should not be retried so return 200 code
            self.assertEqual(200, resp.status_code)
            self.assertIn(case[1], resp.data)  # Assert data substring


class TestGCMNotifications(TestPushNotifications):

    """Tests mobile push notifications."""
    def setUp(self):
        super(TestGCMNotifications, self).setUp()
        self.client = self.app.test_client()
        self.user = fixtures.create_user()
        self.username = self.user.username
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

    def _assert_device_data(self, expected):
        """Verifies device key and active status."""
        # Note: Need to explicitly use username because transaction can be
        #       rolled back and self.user is not bound to a session
        devices = models.Device.get_by_username(self.username, api_args.ANDROID)
        self.assertEqual(expected,
                         [(dev.device_key, dev.active) for dev in devices])

    def test_general_errors(self):
        """Tests general errors for gcm push tasks."""
        self._assert_general_errors('/tasks/push/gcm')

    @mock.patch('gcm.gcm.urllib2.urlopen')
    def test_error_code(self, urlopen_mock):
        """Tests http error codes."""
        taskqueue.add(
            queue_name='push', url='/tasks/push/gcm',
            params=dict(recipient_username=self.user.username,
                        message_type=api_args.NOTIFICATION, message_id=123))
        tasks = self.taskq.get_filtered_tasks(queue_names='push')
        cases = (
            (400, 'The request could not be parsed as JSON'),
            (401, 'There was an error authenticating the sender account'),
            (500, 'GCM service error: 500'),
            (503, 'GCM service is unavailable'))
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
            params=dict(recipient_username=self.user.username,
                        message_type=api_args.NOTIFICATION, message_id=123))
        tasks = self.taskq.get_filtered_tasks(queue_names='push')
        results = [dict(message_id='0:22'), dict(error='Unavailable')]
        gcm_resp = _gcm_response(success=1, failure=1, results=results)
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
            params=dict(recipient_username=self.user.username,
                        message_type=api_args.NOTIFICATION, message_id=123))
        tasks = self.taskq.get_filtered_tasks(queue_names='push')
        results = [dict(message_id='0:22'), dict(error='InvalidRegistration')]
        gcm_resp = _gcm_response(success=1, failure=1, results=results)
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
            params=dict(recipient_username=self.user.username,
                        message_type=api_args.NOTIFICATION, message_id=123))
        tasks = self.taskq.get_filtered_tasks(queue_names='push')
        results = [dict(message_id='0:22', registration_id='55'),
                   dict(error='NotRegistered')]
        gcm_resp = _gcm_response(
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
            params=dict(recipient_username=self.user.username,
                        message_type=api_args.NOTIFICATION, message_id=123))
        tasks = self.taskq.get_filtered_tasks(queue_names='push')
        results = [dict(message_id='0:22'), dict(message_id='0:33')]
        gcm_resp = _gcm_response(success=2, results=results)
        urlopen_mock.return_value = mock.Mock(
            read=mock.Mock(return_value=gcm_resp))
        resp = test_utils.execute_queue_task(self.client, tasks[0])

        # Test request
        req = urlopen_mock.call_args[0][0]
        self.assertEqual(1, urlopen_mock.call_count)
        self.assertEqual(
            'https://android.googleapis.com/gcm/send', req.get_full_url())
        expected_data = dict(
            data=dict(message='sent you a new location', title='Eucaby',
                      type=api_args.NOTIFICATION, id=123),
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
            params=dict(recipient_username=self.user.username,
                        message_type=api_args.NOTIFICATION, message_id=123))
        tasks = self.taskq.get_filtered_tasks(queue_names='push')
        # Newly created device
        models.Device.get_or_create(self.user, '44', api_args.ANDROID)
        results = [dict(message_id='0:22'),  # reg_id='44'
                   dict(message_id='0:33', registration_id='44'),  # reg_id='12'
                   dict(error='NotRegistered')]  # reg_id='23'
        gcm_resp = _gcm_response(success=3, canonical_ids=1, results=results)
        urlopen_mock.return_value = mock.Mock(
            read=mock.Mock(return_value=gcm_resp))
        resp = test_utils.execute_queue_task(self.client, tasks[0])
        # Note: Devices with reg_id '12' and '23' got deactivated
        self._assert_device_data([('44', True)])
        self.assertEqual(200, resp.status_code)


class TestAPNsNotifications(TestPushNotifications):

    """Tests APNs mobile push notifications."""
    def setUp(self):
        super(TestAPNsNotifications, self).setUp()
        self.client = self.app.test_client()
        self.user = fixtures.create_user()
        self.username = self.user.username
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
            ('12', api_args.ANDROID), ('23', api_args.IOS),
            ('34', api_args.IOS)]
        self.devices = [models.Device.get_or_create(
            self.user, *param) for param in device_params]

    def test_general_errors(self):
        """Tests general errors for apns push tasks."""
        self._assert_general_errors('/tasks/push/apns')

    @mock.patch('eucaby_api.tasks.api_utils.create_apns_socket')
    @mock.patch('eucaby_api.tasks.apns.Payload')
    @mock.patch('eucaby_api.tasks.apns.Frame.add_item')
    def test_success(self, mock_add_item, mock_payload, mock_create_socket):
        """Tests sending push notifications to iOS devices."""
        apns_socket = mock.Mock()
        mock_create_socket.return_value = apns_socket
        taskqueue.add(
            queue_name='push', url='/tasks/push/apns',
            params=dict(
                recipient_username=self.user.username, sender_name='Name',
                message_type=api_args.NOTIFICATION, message_id=123))
        tasks = self.taskq.get_filtered_tasks(queue_names='push')

        resp = test_utils.execute_queue_task(self.client, tasks[0])
        self.assertEqual(200, resp.status_code)

        mock_payload.assert_called_with(
            sound='default', alert='Name\nsent you a new location',
            custom=dict(type=api_args.NOTIFICATION, id=123))
        self.assertEqual(2, mock_add_item.call_count)  # For every iOS device
        mock_send_notif = apns_socket.gateway_server.send_notification_multiple
        self.assertEqual(1, mock_send_notif.call_count)


class TestCleanupiOSDevicesTask(test_base.TestCase):

    def setUp(self):
        super(TestCleanupiOSDevicesTask, self).setUp()
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
            ('12', api_args.ANDROID), ('23', api_args.IOS),
            ('34', api_args.IOS)]
        self.devices = [models.Device.get_or_create(
            self.user, *param) for param in device_params]

    @mock.patch('eucaby_api.tasks.api_utils.create_apns_socket')
    def test_cleanup_devices(self, mock_create_socket):
        """Tests cleanup ios devices."""
        apns_socket = mock.Mock(
            feedback_server={
                '12': mock.Mock(), '23': mock.Mock(), '34': mock.Mock()})
        mock_create_socket.return_value = apns_socket

        # Execute cron job
        resp = self.client.get('/tasks/push/apns/cleanup',
                               headers={'X-Appengine-Cron': 'true'})
        self.assertEqual(200, resp.status_code)
        self.assertIn(
            'The following iOS devices are subject to cleanup',
            resp.data)
        devices = models.Device.get_by_username(self.user.username)
        # iOS devices are deactivated
        self.assertEqual(1, len(devices))
        self.assertEqual(self.devices[0].device_key, devices[0].device_key)


if __name__ == '__main__':
    unittest.main()
