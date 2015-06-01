import unittest

from eucaby_api import app as eucaby_app
from eucaby_api.utils import reqparse


class RequestParserTest(unittest.TestCase):

    def setUp(self):
        self.app = eucaby_app.create_app()
        self.app.config.from_object('eucaby_api.config.Testing')

    def test_parse_args(self):
        arg1 = reqparse.Argument('param1')
        arg2 = reqparse.Argument('param2', required=True)
        parser = reqparse.RequestParser()
        parser.add_argument(arg1)
        parser.add_argument(arg2)
        with self.app.test_request_context(
            '?param1=test1&param2=test2&param3=test3'):
            parsed_args = dict(param1='test1', param2='test2')
            # Non-strict
            args = parser.parse_args()
            self.assertEqual(parsed_args, args)
            # Strict
            self.assertRaises(reqparse.InvalidError, parser.parse_args,
                              strict=True)
            try:
                parser.parse_args(strict=True)
            except reqparse.InvalidError as ex:
                self.assertEqual({}, ex.errors)
                self.assertEqual(parsed_args, ex.namespace)
                self.assertEqual(
                    dict(param3='Unrecognized parameter'), ex.unparsed)

    def test_clean_args(self):
        """Tests clean_args function."""
        # XXX: Implement
        pass


class ArgumentParserTest(unittest.TestCase):

    def test_handle_validation_error(self):
        arg = reqparse.Argument('some_param')
        self.assertRaises(
            ValueError, arg.handle_validation_error, 'some_error')


if __name__ == '__main__':
    unittest.main()
