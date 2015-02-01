
import flask
from flask import json
import flask_restful

CODE_ERRORS = {
    405: 'invalid_method',
    401: 'invalid_auth'
}

def output_json(data, code, headers=None):
    """Custom json output."""
    if code not in (200, 201) and 'code' not in data:
        # oauthlib returns response with status and message,
        #   e.g. {'status': 401, 'message': 'Unauthorized'}
        # If code is in data then response is probably in the correct format
        # Note: status and message should always be present
        assert 'status' in data
        assert 'message' in data
        # Need to customize the error fields
        data.pop('status')
        resp_code = 'invalid_request'
        if code in CODE_ERRORS:
            resp_code = CODE_ERRORS[code]
        data['code'] = resp_code
        data['message'] = data['message'].capitalize()
    resp = flask.make_response(json.dumps(data), code)
    resp.headers.extend(headers or {})
    return resp


class Api(flask_restful.Api):
    def __init__(self, *args, **kwargs):
        super(Api, self).__init__(*args, **kwargs)
        self.representations = {
            'application/json': output_json
        }
