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
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_taskqueue_stub(root_path='.')
        self.taskq = self.testbed.get_stub(
            testbed.TASKQUEUE_SERVICE_NAME)
        # Create devices
        device_params = [('12', api_args.ANDROID), ('34', api_args.IOS)]
        # for user in [self.user, self.user2]:
        for param in device_params:  # Both users own both devices
            models.Device.get_or_create(self.user, *param)
        self.payload_data = dict(
            title=u'Test Юзер', message='sent you a new location')

    def tearDown(self):
        super(GaeUtilsTest, self).tearDown()
        self.testbed.deactivate()

    def test_send_notifications(self):
        """Tests send notifications."""
        # Send notification
        gae_utils.send_notification(
            self.user.username, u'Test Юзер', api_args.LOCATION)

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
            mock_send_notif = (apns_socket.gateway_server.
                               send_notification_multiple)
            resp_ios = test_utils.execute_queue_task(self.client, tasks[1])
            self.assertEqual(1, mock_send_notif.call_count)
            self.assertEqual(200, resp_ios.status_code)


if __name__ == '__main__':
    unittest.main()