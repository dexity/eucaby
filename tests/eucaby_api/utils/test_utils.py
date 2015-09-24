# -*- coding: utf-8 -*-

import datetime
import itertools
import unittest

from eucaby_api import args as api_args
from eucaby_api import app as eucaby_app
from eucaby_api.utils import utils as api_utils
from eucaby_api.utils import date as date_utils

from tests.eucaby_api import base as test_base


class UtilsTest(unittest.TestCase):

    def setUp(self):
        self.app = eucaby_app.create_app()
        self.app.config.from_object(test_base.Testing)
        self.cases = (
            (None, '', ''),  # Empty parameters
            (u'Юзер', '', ''),  # Name parameter is set
            (None, 'something', '123'),  # Message type and id are set
            (u'Юзер', api_args.NOTIFICATION, 123))  # All parameters are set

    def test_payload_data(self):
        """Tests payload data."""
        excepted = (
            dict(title='Eucaby', message='New incoming messages'),
            dict(title=u'Юзер', message='New incoming messages'),
            dict(title='Eucaby', message='sent you a new something'),
            dict(title=u'Юзер', message='sent you a new location'))
        for i, case in enumerate(self.cases):
            data = api_utils.payload_data(*case[:2])
            self.assertEqual(excepted[i], data)

    def test_gcm_payload_data(self):
        """Tests GCM payload data."""
        excepted = (
            dict(title='Eucaby', message='New incoming messages',
                 type='', id=''),
            dict(title=u'Юзер', message='New incoming messages',
                 type='', id=''),
            dict(title='Eucaby', message='sent you a new something',
                 type='something', id='123'),
            dict(title=u'Юзер', message='sent you a new location',
                 type='notification', id=123))
        for i, case in enumerate(self.cases):
            data = api_utils.gcm_payload_data(*case)
            self.assertEqual(excepted[i], data)

    def test_apns_payload_data(self):
        """Tests APNs payload data."""
        excepted = (
            dict(alert='Eucaby\nNew incoming messages', sound='default',
                 custom=dict(type='', id='')),
            dict(alert=u'Юзер\nNew incoming messages', sound='default',
                 custom=dict(type='', id='')),
            dict(alert='Eucaby\nsent you a new something', sound='default',
                 custom=dict(type='something', id='123')),
            dict(alert=u'Юзер\nsent you a new location', sound='default',
                 custom=dict(type='notification', id=123)))
        for i, case in enumerate(self.cases):
            data = api_utils.apns_payload_data(*case)
            self.assertEqual(excepted[i], data)

    def test_create_key(self):
        """Tests create key."""
        # No arguments
        self.assertEqual('', api_utils.create_key())
        # Arguments with numbers
        self.assertEqual(
            'test::123::{\'hello\': \'world\'}',
            api_utils.create_key('test', 123, dict(hello='world')))
        # Typical scenario
        self.assertEqual('user::settings',
                         api_utils.create_key('user', 'settings'))

    def test_json_to_dict(self):
        """Tests json to dict converter."""
        # Invalid json
        self.assertEqual({}, api_utils.json_to_dict(''))
        self.assertEqual({}, api_utils.json_to_dict(None))
        # Valid json
        self.assertEqual(dict(hello='world'),
                         api_utils.json_to_dict('{"hello": "world"}'))

    def test_dt2ts(self):
        """Tests datetime to timestamp util."""
        self.assertRaises(AttributeError, date_utils.dt2ts, None)
        date_time = datetime.datetime(2015, 8, 16, 11, 41)
        self.assertEqual(1439750460000, date_utils.dt2ts(date_time))
        self.assertEqual(1439750460, date_utils.dt2ts(date_time, in_ms=False))

    def _assert_sorted(self, list1, list2, result, key, reverse):
        """Asserts sorted elements after merge."""
        for i in range(20):
            il1 = itertools.chain(list1)
            il2 = itertools.chain(list2)
            self.assertEqual(
                result[:i+1],
                api_utils.merge_sorted_queries(
                    [il1, il2], i+1, key, reverse=reverse))

    def test_merge_sorted_queries_numbers(self):
        """Tests merging sorted queries."""
        # Direct order
        list1 = [1, 3, 4, 7, 10]
        list2 = [2, 5, 6, 10, 11, 12]
        result = [1, 2, 3, 4, 5, 6, 7, 10, 10, 11, 12]
        self._assert_sorted(list1, list2, result, lambda x: x, False)
        # Reverse order
        list1.reverse()
        list2.reverse()
        result.reverse()
        self._assert_sorted(list1, list2, result, lambda x: x, True)

    def test_merge_sorted_queries_class(self):
        """Tests merging sorted queries."""
        class Data(object):
            def __init__(self, dt):
                self.created_date = dt

            def __str__(self):
                return str(self.created_date)

        now = datetime.datetime(2015, 8, 1)
        delta = datetime.timedelta
        # Direct order
        list1 = [Data(now + delta(seconds=sec)) for sec in [1, 3, 4, 7, 10]]
        list2 = [Data(now + delta(seconds=sec))
                 for sec in [2, 5, 6, 10, 11, 12]]
        items = itertools.chain(list1, list2)
        result = sorted(items, key=lambda x: x.created_date, reverse=False)
        self._assert_sorted(
            list1, list2, result, lambda x: x.created_date, False)

        # Reverse order
        list1.reverse()
        list2.reverse()
        result.reverse()
        # There is disambiguation with number 10 so we will just switch them
        tmp = result[2]
        result[2] = result[3]
        result[3] = tmp
        self._assert_sorted(
            list1, list2, result, lambda x: x.created_date, True)


if __name__ == '__main__':
    unittest.main()
