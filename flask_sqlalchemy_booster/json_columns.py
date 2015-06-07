from sqlalchemy.types import TypeDecorator, TEXT
from sqlalchemy.ext.mutable import Mutable
from flask.json import _json as json
from .json_encoder import json_encoder


class JSONEncodedStruct(TypeDecorator):
    "Represents an immutable structure as a json-encoded string."

    impl = TEXT

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value, default=json_encoder)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class MutableDict(Mutable, dict):
    @classmethod
    def coerce(cls, key, value):
        "Convert plain dictionaries to MutableDict."

        if not isinstance(value, MutableDict):
            if isinstance(value, dict):
                return MutableDict(value)

            # this call will raise ValueError
            return Mutable.coerce(key, value)
        else:
            return value

    def __setitem__(self, key, value):
        "Detect dictionary set events and emit change events."

        dict.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        "Detect dictionary del events and emit change events."

        dict.__delitem__(self, key)
        self.changed()


class MutableList(Mutable, list):
    @classmethod
    def coerce(cls, key, value):
        "Convert plain lists to MutableList."

        if not isinstance(value, MutableList):
            if isinstance(value, list):
                return MutableList(value)

            # this call will raise ValueError
            return Mutable.coerce(key, value)
        else:
            return value

    def __setitem__(self, key, value):
        "Detect set events and emit change events."

        list.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        "Detect del events and emit change events."

        list.__delitem__(self, key)
        self.changed()

    def append(self, value):
        "Detect append events and emit change events."

        list.append(self, value)
        self.changed()
