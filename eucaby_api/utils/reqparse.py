
from flask import request
from flask.ext.restful import reqparse
from werkzeug import exceptions

class InvalidError(Exception):

    def __init__(self, errors, namespace, unparsed, *args, **kwargs):
        self.errors = errors
        self.namespace = namespace
        self.unparsed = unparsed
        super(InvalidError, self).__init__(*args, **kwargs)


class Argument(reqparse.Argument):

    def handle_validation_error(self, error):
        msg = self.help or str(error)
        raise ValueError(msg)


class RequestParser(reqparse.RequestParser):

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
            except ValueError as e:
                self.errors[arg.dest or arg.name] = str(e)

        # Collect unparsed (extra) arguments
        if strict and req.unparsed_arguments:
            for arg, value in req.unparsed_arguments.items():
                self.unparsed[arg] = 'Unrecognized parameter'

        if self.errors or self.unparsed:
            raise InvalidError(self.errors, namespace, self.unparsed)
        return namespace
