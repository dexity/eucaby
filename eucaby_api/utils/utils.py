"""Api utils."""

import uuid
from flask import json
from flask import jsonify
import flask_restful


PARAM_MISSING = 'Missing {param} parameter'
SUCCESS_STATUSES = (200, 201)

class Object(object):
    def __init__(self, **entries):
        self.__dict__.update(entries)


def make_response(resp_dict, status_code):
    """This wrapper for flask json response."""
    resp_dict = resp_dict or {}
    resp = jsonify(**resp_dict)
    resp.status_code = status_code
    return resp


def convert_oauthlib_error(code, description=''):
    """Converts oauthlib code and description to eucaby response."""
    def _missing(param_, code_, message_, field_message_):
        return dict(
            message=message_, code=code_, fields={param_: field_message_}), 400

    if code == 'unsupported_grant_type':
        return _missing(
            'grant_type', code, 'Grant type is not supported',
            'Grant type is missing or invalid')
    elif code == 'invalid_request':
        params = ('service', 'password', 'username', 'grant_type', 'scope',
                  'refresh_token')
        for param in params:
            # Hack to match invalid_request description with the fields
            key = param.replace('_', ' ')
            if key in description:
                return _missing(
                    param, code, description, PARAM_MISSING.format(param=param))
    return None


def format_oauthlib_response(resp):
    """Formats oauthlib response.

    Args:
        resp:  Instance of Flask Response
    """
    if resp.status_code in SUCCESS_STATUSES:
        return resp
    data = json.loads(resp.data)
    message = ''
    if 'error_description' in data:
        message = data['error_description']
    error_code = data['error']
    resp = convert_oauthlib_error(error_code, message)
    if resp is not None:
        return make_response(*resp)
    error = dict(message=message, code=error_code)
    return make_response(error, 403)


def format_fb_response(resp, fields):
    """Formats Facebook error responses.

    Args:
        resp: Instance of flask_oauthlib OAuthResponse
    """
    if resp.status in SUCCESS_STATUSES:
        return flask_restful.marshal(resp.data, fields)
    elif 'code' in resp.data:
        return resp
    return (dict(message=resp.data['error']['message'], code='service_error'),
            resp.status)


def generate_uuid(is_hex=True):
    """Generates uuid in hex form."""
    s = uuid.uuid4()
    if is_hex:
        return s.hex
    return str(s)


def zone2offset(zone):
    """Converts timezone hour to offset minute."""
    return zone*60
