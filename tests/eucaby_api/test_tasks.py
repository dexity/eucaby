# -*- coding: utf-8 -*-

import flask
import unittest

from google.appengine.api import taskqueue
from google.appengine.ext import testbed

from eucaby_api import models

from tests.eucaby_api import fixtures
from tests.eucaby_api import base as test_base
from tests.utils import utils as test_utils


class TestPushNotifications(test_base.TestCase):

    """Tests mobile push notifications."""
    def setUp(self):
        super(TestPushNotifications, self).setUp()
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

    def tearDown(self):
        self.testbed.deactivate()

    def test_general_errors(self):
        """Tests general errors for push tasks."""
        # No parameter recipient_username
        taskqueue.add(queue_name='push', url='/tasks/push')
        tasks = self.taskq.get_filtered_tasks(queue_names='push')
        self.assertEqual(1, len(tasks))
        resp = test_utils.execute_queue_task(self.client, tasks[0])
        self.assertEqual(400, resp.status_code)
        self.assertEqual('Missing recipient_username parameter', resp.data)

        # Either user or device, or user device found
        taskqueue.add(
            queue_name='push', url='/tasks/push',
            params=dict(recipient_username='unknown'))
        tasks = self.taskq.get_filtered_tasks(queue_names='push')
        resp = test_utils.execute_queue_task(self.client, tasks[1])
        self.assertEqual(404, resp.status_code)
        self.assertEqual('User device not found', resp.data)

    def test_push_notifications(self):
        """Tests push notifications to Android and iOS devices."""
        # Create android
        # Emulator
        # device_key = 'APA91bG3cjvIJNeVVL6iBgdFoMh_oN7oM6UsSE8mMrGgKs_VtQA-Y033YN3I8UIjrgqnaetF7faQTkHeKAg11thX4fnz3ZTjQPBUjlD8SskmqltveElYUdOKhYXNe5NH5FIBRTtk49o2ftbhNxe93sQptAL1Wy85nA'
        # Real device
        device_key = 'APA91bF8dt3RbUriN4zZdI7qMHPCCndJH4_tyiYvsmIBR1FAP6Rp1Q5zEOtOAYvsq9e0epYgBwHsM8z3-LJLiETVKaSpclam6gu1TUFESxaUKI3qRnUCa1K_zLsV0E-vRNz9eaoWdvfSHNH-zcWOGmLs2VkdacoYWQ'
        dev = models.Device.get_or_create(
            self.user, device_key=device_key, platform='android')

        # Create iOS
        device_key = 'baa0b38b8324d14c38041eae955d0a3e258297df519fab9a22bb4d2655d12197'
        dev2 = models.Device.get_or_create(
            self.user, device_key=device_key, platform='ios')

        taskqueue.add(
            queue_name='push', url='/tasks/push',
            params=dict(recipient_username=self.user.username))
        tasks = self.taskq.get_filtered_tasks(queue_names='push')
        self.assertEqual(1, len(tasks))
        test_utils.execute_queue_task(self.client, tasks[0])


if __name__ == '__main__':
    unittest.main()