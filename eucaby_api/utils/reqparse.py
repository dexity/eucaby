"""Custom request parser."""

from flask import request
from flask_restful import reqparse

from eucaby_api.utils import utils as api_utils


class InvalidError(Exception):

    """Custom InvalidError exception."""

    def __init__(self, errors, namespace, unparsed, *args, **kwargs):
        self.errors = errors
        self.namespace = namespace
        self.unparsed = unparsed
        super(InvalidError, self).__init__(*args, **kwargs)


class Argument(reqparse.Argument):

    """Argument class with custom error validation."""

    def handle_validation_error(self, error):
        msg = self.help or str(error)
        raise ValueError(msg)


class RequestParser(reqparse.RequestParser):

    """RequestParser class with custom parse_args."""

    def __init__(self, argument_class=Argument,
                 namespace_class=reqparse.Namespace):
        self.errors = {}
        self.unparsed = {}
        super(RequestParser, self).__init__(argument_class, namespace_class)

    def parse_args(self, req=None, strict=False):
        """Argument parser which returns parsed arguments or error."""
        if req is None:
            req = request

        namespace = self.namespace_class()

        # A record of arguments not yet parsed; as each is found
        # among self.args, it will be popped out
        req.unparsed_arguments = dict(Argument('').source(req))

        for arg in self.args:
            try:
                value, found = arg.parse(req)
                if found or arg.store_missing:
                    namespace[arg.dest or arg.name] = value
            except ValueError as ex:
                self.errors[arg.dest or arg.name] = str(ex)

        # Collect unparsed (extra) arguments
        if strict and req.unparsed_arguments:
            for arg, value in req.unparsed_arguments.items():
                self.unparsed[arg] = 'Unrecognized parameter'

        if self.errors or self.unparsed:
            raise InvalidError(self.errors, namespace, self.unparsed)
        return namespace


def clean_args(args, strict=False, is_task=False):
    """Simple parsing handler.

    Returns:
        Dictionary of arguments or error response.
    """
    parser = RequestParser()
    for arg in args:
        parser.add_argument(arg)
    try:
        return parser.parse_args(strict=strict)
    except InvalidError as e:
        errors = e.errors
        if strict:
            errors.update(e.unparsed)
        error = dict(message='Invalid request parameters',
                     code='invalid_request', fields=errors)
        # For tasks even if the error occurs it should return 200 status code
        # to avoid resubmitting the task
        status_code = (is_task and 200) or 400
        return api_utils.make_response(error, status_code)
