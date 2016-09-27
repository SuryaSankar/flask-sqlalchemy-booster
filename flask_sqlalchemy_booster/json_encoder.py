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
    elif isinstance(obj, int) or isinstance(obj, long) or isinstance(obj, float):
        return obj
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, unicode):
        return obj
    elif isinstance(obj, OrderedDict):
        return [[k, json_encoder(v)]
                for k, v in obj.items()
                if not (k == 'key' and isinstance(v, FunctionType))]
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


class BoosterJSONEncoder(_json.JSONEncoder):
    def default(self, obj):
        return json_encoder(obj)


def booster_json_decoder(obj):
    if '__type__' in obj:
        if obj['__type__'] == '__datetime__':
            return datetime.fromtimestamp(obj['epoch'])
    return obj


# Encoder function
def booster_json_dumps(obj):
    return _json.dumps(obj, cls=BoosterJSONEncoder)


# Decoder function
def booster_json_loads(obj):
    return _json.loads(obj, object_hook=booster_json_decoder)
