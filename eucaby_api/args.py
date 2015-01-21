"""Request arguments for API."""

import re
from eucaby_api.utils import reqparse

EMAIL_REGEX_PATTERN = '^[A-Z0-9\._%+-]+@[A-Z0-9\.-]+\.[A-Z]{2,4}$'  # pylint: disable=anomalous-backslash-in-string
EMAIL_REGEX = re.compile(EMAIL_REGEX_PATTERN, flags=re.IGNORECASE)
MISSING_EMAIL_USERNAME = 'Missing email or username parameters'


class ValidationError(Exception):
    pass


def email(email_str):
    if EMAIL_REGEX.match(email_str):
        return email_str
    raise ValidationError("{} is not a valid email")


REQUEST_LOCATION_ARGS = [
    reqparse.Argument(name='email', type=email, help=MISSING_EMAIL_USERNAME),
    reqparse.Argument(name='username', type=str, help=MISSING_EMAIL_USERNAME)
]
