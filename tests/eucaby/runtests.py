
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.eucaby.test_settings')

import django

from django.conf import settings
from django.test import utils as test_utils

django.setup()


if __name__ == '__main__':
    TestRunner = test_utils.get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['core'])
