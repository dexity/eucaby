
import flask
from flask import json
import flask_restful

CODE_ERRORS = {
    405: 'invalid_method'
}

def output_json(data, code, headers=None):
    """Custom json output."""
    if code != 200:
        # Customize error fields
        assert 'status' in data
        assert 'message' in data
        # Note: status and message should always be present
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
