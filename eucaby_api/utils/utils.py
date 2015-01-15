"""Api utils."""

from flask import jsonify

def make_response(resp_dict, status_code):
    """Returns error response in JSON format."""
    resp_dict = resp_dict or {}
    resp = jsonify(**resp_dict)
    resp.status_code = status_code
    return resp
