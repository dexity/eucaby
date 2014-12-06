import unittest
from eucaby_api import wsgi
from eucaby_api import auth

class AuthTest(unittest.TestCase):

    def setUp(self):
        self.app = wsgi.create_app()
        self.app.config.from_object('eucaby_api.config.Testing')
        self.app.secret_key = 'development'

    def test_fb_exchange_token(self):
        ctx = self.app.test_request_context()
        ctx.push()
        auth.fb_exchange_token()

    def test_fb_refresh_token(self):
        pass



if __name__ == "__main__":
    unittest.main()
