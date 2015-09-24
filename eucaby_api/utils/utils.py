"""Api utils."""

import apns
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


def payload_data(name, msg_type):
    """Creates payload data for GCM message."""
    title = name or 'Eucaby'
    message = 'New incoming messages'
    if msg_type:
        if msg_type == 'notification':
            msg_type = 'location'
        message = 'sent you a new ' + msg_type
    return dict(title=title, message=message)


def gcm_payload_data(name, msg_type, msg_id):
    """Creates payload data for GCM message."""
    data = payload_data(name, msg_type)
    data.update(dict(type=msg_type, id=msg_id))
    return data


def apns_payload_data(name, msg_type, msg_id):
    """Creates payload data for APNs message."""
    data = payload_data(name, msg_type)
    return dict(
        alert=u'{title}\n{message}'.format(**data), sound='default',
        custom=dict(type=msg_type, id=msg_id))  # Additional payload parameters


def create_apns_socket(app):
    """Creates APNs socket. App should be configured at the stage."""
    return apns.APNs(
        use_sandbox=app.config['APNS_USE_SANDBOX'],
        cert_file=app.config['APNS_CERT_FILE'],
        key_file=app.config['APNS_KEY_FILE'])#, enhanced=True)


def create_key(*args):
    """Creates key for memcached."""
    return '::'.join([str(arg) for arg in args])


def json_to_dict(json_str):
    """Convenience function to convert json string to dictionary."""
    try:
        return json.loads(json_str)
    except (TypeError, ValueError):
        return {}


def merge_sorted_queries(queries, size, key, reverse=False):
    """Merges several sorted queries into one list."""
    # Note: Queries are already sorted in certain order. Make sure that
    #       reverse matches the sorting order. Otherwise unexpected results
    #       will occur.
    #       Queries should be iterable (support .next() interface)
    def compare(x, y, _key, _reverse):
        """Compares two elements."""
        if _reverse:
            return _key(x) > _key(y)
        return _key(x) < _key(y)

    queries_size = len(queries)
    assert queries_size > 0
    current_list = [None for _ in range(queries_size)]
    empty_list = [False for _ in range(queries_size)]
    k = 0
    items = []
    while k < size:
        # All lists are processed
        if len(set(empty_list)) == 1 and empty_list[0]:
            break
        curr = None
        idx = 0
        for i, query in enumerate(queries):
            if empty_list[i]:
                continue
            try:
                if current_list[i] is None:
                    next_item = query.next()
                    # No query item can be None
                    if next_item is None:
                        raise
                    current_list[i] = next_item
            except StopIteration:
                empty_list[i] = True
            if (curr is None or
                    (current_list[i] is not None and
                     compare(current_list[i], curr, key, reverse))):
                curr = current_list[i]
                idx = i
        if curr is not None:
            items.append(curr)
            current_list[idx] = None
        k += 1
    return items
