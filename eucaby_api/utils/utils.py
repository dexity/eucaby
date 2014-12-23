
import uuid
from flask import jsonify

def make_error(error_dict, status_code=400):
    """Returns error response in JSON format."""
    error_dict = error_dict or {}
    resp = jsonify(**error_dict)
    resp.status_code = status_code
    return resp


def generate_uuid(is_hex=True):
    s = uuid.uuid4()
    if is_hex:
        return s.hex
    return str(s)
