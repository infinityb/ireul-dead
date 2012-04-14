from sqlalchemy.types import TypeDecorator, VARCHAR
import json
import audiotools

class JSONEncodedDict(TypeDecorator):
    """
    Represents an immutable structure as a json-encoded string.

    Usage::

        JSONEncodedDict(255)

    """

    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)

        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class EncodingParams(JSONEncodedDict):

    def process_result_value(self, value, dialect):
        value = super(EncodingParams, self).process_result_value(value, dialect)
        if value is not None:
            value = audiotools.EncodingParams(**value)
        return value
