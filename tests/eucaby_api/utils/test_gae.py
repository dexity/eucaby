# -*- coding: utf-8 -*-

import mock
import unittest

from google.appengine.ext import testbed

from eucaby_api import args as api_args
from eucaby_api import models
from eucaby_api.utils import gae as gae_utils
from tests.eucaby_api import base as test_base
from tests.eucaby_api import fixtures
from tests.utils import utils as test_utils


class GaeUtilsTest(test_base.TestCase):

    def setUp(self):
        super(GaeUtilsTest, self).setUp()
        self.client = self.app.test_client()
        self.user = fixtures.create_user()
        self.testbed = test_utils.create_testbed()
        self.taskq = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
        self.mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)
        # Create devices
        device_params = [('12', api_args.ANDROID), ('34', api_args.IOS)]
        for param in device_params:  # Both users own both devices
            models.Device.get_or_create(self.user, *param)
        self.payload_data = dict(
            title=u'Test Юзер', message='sent you a new location',
            type='notification', id=123)

    def tearDown(self):
        super(GaeUtilsTest, self).tearDown()
        self.testbed.deactivate()

    def test_send_notifications(self):
        """Tests send notifications."""
        # Send notification
        gae_utils.send_notification(
            self.user.username, u'Test Юзер', api_args.NOTIFICATION, 123)

        # Verify result
        tasks = self.taskq.get_filtered_tasks(queue_names='push')
        assert 2 == len(tasks)
        # Android task
        with mock.patch('eucaby_api.tasks.gcm.GCM.json_request') as req_mock:
            req_mock.return_value = {}
            resp_android = test_utils.execute_queue_task(self.client, tasks[0])

            # Test GCM request
            self.assertEqual(1, req_mock.call_count)
            req_mock.assert_called_with(
                registration_ids=['12'], data=self.payload_data, retries=7)
            self.assertEqual(200, resp_android.status_code)

        # iOS task
        with mock.patch(
            'eucaby_api.tasks.api_utils.create_apns_socket'
        ) as mock_create_socket:
            apns_socket = mock.Mock()
            mock_create_socket.return_value = apns_socket
            # Test APNs request
            # Note: We currently use send_notification for APNs. Fix test
            #       when using send_notification_multiple.
            #       See comments for the method.
            # mock_send_notif = (apns_socket.gateway_server.
            #                    send_notification_multiple)
            mock_send_notif = apns_socket.gateway_server.send_notification
            resp_ios = test_utils.execute_queue_task(self.client, tasks[1])
            self.assertEqual(1, mock_send_notif.call_count)
            self.assertEqual(200, resp_ios.status_code)

    @mock.patch('eucaby_api.utils.gae.taskqueue.add')
    def test_send_mail(self, add_mock):  # pylint: disable=no-self-use
        """Tests send email."""
        gae_utils.send_mail(
            'Some subject', u'Текст сообщения', ['test@example.com'])
        add_mock.assert_called_with(
            url='/tasks/mail', queue_name='mail',
            params={'body': u'Текст сообщения',
                    'recipient': ['test@example.com'],
                    'subject': 'Some subject'})


if __name__ == '__main__':
    unittest.main()
