from __future__ import absolute_import
from flask.testing import FlaskClient
from flask.json import _json as json
from .json_encoder import json_encoder
from toolspy import merge


class FlaskClientBooster(FlaskClient):


    def jread(self, resp):
        return json.loads(resp.data)

    def jpost(self, url, data, **kwargs):
        kwargs['content_type'] = "application/json"
        jdata = json.dumps(data, default=json_encoder)
        parse_json_response = kwargs.pop('parse_json_response', True)
        resp = self.post(url, data=jdata, **kwargs)
        return json.loads(resp.data) if parse_json_response else resp

    def jput(self, url, data, **kwargs):
        kwargs['content_type'] = "application/json"
        jdata = json.dumps(data, default=json_encoder)
        parse_json_response = kwargs.pop('parse_json_response', True)
        resp = self.put(url, data=jdata, **kwargs)
        return json.loads(resp.data) if parse_json_response else resp

    def jpatch(self, url, data, **kwargs):
        kwargs['content_type'] = "application/json"
        jdata = json.dumps(data, default=json_encoder)
        parse_json_response = kwargs.pop('parse_json_response', True)
        resp = self.patch(url, data=jdata, **kwargs)
        return json.loads(resp.data) if parse_json_response else resp


    def jget(self, *args, **kwargs):
        return self.jread(self.get(*args, **kwargs))

    def upload(self, url, file_key, file_path, **kwargs):
        buffered = kwargs.pop('buffered', True)
        content_type = kwargs.pop('content_type', 'multipart/form-data')
        kwargs['data'] = merge(
            kwargs['data'],
            {file_key: (open(file_path, 'rb'), file_path)})
        return self.post(url, buffered=buffered, content_type=content_type,
                         **kwargs)
