from datetime import datetime
from decimal import Decimal
from flask.json import _json
from toolspy import dict_map
from .utils import is_list_like, is_dict_like
from collections import OrderedDict
from types import FunctionType


def json_encoder(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, OrderedDict):
        return [[k, json_encoder(v)]
                for k, v in obj.items()
                if not (k == 'key' and isinstance(v, FunctionType))]
    elif isinstance(obj, Decimal):
        return str(obj)
    elif isinstance(obj, unicode):
        return obj
    elif hasattr(obj, 'todict'):
        return obj.todict()
    elif is_list_like(obj):
        return [json_encoder(i) for i in obj]
    elif is_dict_like(obj):
        return dict_map(obj, lambda v: json_encoder(v))
    else:
        try:
            return _json.JSONEncoder().default(obj)
        except:
            return unicode(obj)
