import unittest
import flask
from eucaby_api import wsgi

class TestViews(unittest.TestCase):

    def setUp(self):
        wsgi.app.config['TESTING'] = True
        self.app = wsgi.app.test_client()

    def tearDown(self):
        pass

    def testAccessToken(self):
        # Get is not supported
        resp = self.app.get('/oauth/token')
        self.assertEqual(405, resp._status_code)
        #
        resp = self.app.post('/oauth/token')
        print resp._status_code

        resp = self.app.post(
            '/oauth/token', data=dict(
                service='facebook', grant_type='password', username='test_user',
                password='test_token'))
        self.assertEqual(200, resp._status_code)
        # XXX: Add Facebook mock


if __name__ == "__main__":
    unittest.main()
