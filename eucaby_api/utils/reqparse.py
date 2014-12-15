from flask import request
from flask.ext.restful import reqparse


class InvalidError(Exception):

    def __init__(self, errors, namespace, *args, **kwargs):
        self.errors = errors
        self.namespace = namespace
        super(InvalidError, self).__init__(*args, **kwargs)


class Argument(reqparse.Argument):

    def handle_validation_error(self, error):
        msg = self.help if self.help is not None else str(error)
        raise ValueError(msg)


class RequestParser(reqparse.RequestParser):

    def __init__(self, argument_class=Argument,
                 namespace_class=reqparse.Namespace):
        self.errors = {}
        super(RequestParser, self).__init__(argument_class, namespace_class)

    def parse_args(self, req=None):
        """Argument parser which returns parsed arguments or error."""
        if req is None:
            req = request

        namespace = self.namespace_class()

        for arg in self.args:
            try:
                value, found = arg.parse(req)
                if found or arg.store_missing:
                    namespace[arg.dest or arg.name] = value
            except ValueError as e:
                self.errors[arg.dest or arg.name] = str(e)

        if self.errors:
            raise InvalidError(self.errors, namespace)

        return namespace