import unittest
from eucaby_api import args


class TestArgs(unittest.TestCase):

    def test_email_regex(self):
        self.assertTrue(args.email('test@example.com'))
        self.assertTrue(args.email('test.1@example.com'))
        self.assertRaises(args.ValidationError, args.email, 'test@@example.com')
        self.assertRaises(args.ValidationError, args.email, 'test.example.com')


    def test_latlng(self):
        self.assertTrue(args.latlng('123,456'))
        self.assertTrue(args.latlng('123.,456.'))
        self.assertTrue(args.latlng('123.03,456.00'))
        self.assertTrue(args.latlng('-123,456'))
        self.assertTrue(args.latlng('123.,-456.'))
        self.assertTrue(args.latlng('-123.03,-456.00'))
        self.assertRaises(args.ValidationError, args.latlng, '123')
        self.assertRaises(args.ValidationError, args.latlng, '123.456')
        self.assertRaises(args.ValidationError, args.latlng, '123a,456')
        self.assertRaises(args.ValidationError, args.latlng, '123,456,4')


if __name__ == '__main__':
    unittest.main()
