from flask.views import MethodView
from .responses import process_args_and_render_json_list, process_args_and_render_json_obj, success_json, error_json
from flask import g
from schemalite import SchemaError


class CrudApiView(MethodView):

    _model_class_ = None
    _list_query_ = None
    _id_key_ = 'id'
    _schema_for_post_ = None
    _schema_for_put_ = None

    def get(self, _id):
        list_query = self._list_query_ or self._model_class_.query
        if _id is None:
            return process_args_and_render_json_list(list_query)
        else:
            return process_args_and_render_json_obj(
                self._model_class_.get(_id, key=self._id_key_))

    def post(self):
        if self._schema_for_post_:
            try:
                self._schema_for_post_.validate(g.json)
            except SchemaError as e:
                return error_json(400, e.value)
            json_data = self._schema_for_post_.adapt(g.json)
        else:
            json_data = g.json
        return process_args_and_render_json_obj(
            self._model_class_.create(**json_data))

    def put(self, _id):
        obj = self._model_class_.get(_id, key=self._id_key_)
        if self._schema_for_put_:
            try:
                self._schema_for_put_.validate(g.json)
            except SchemaError as e:
                return error_json(400, e.value)
            json_data = self._schema_for_put_.adapt(g.json)
        else:
            json_data = g.json
        return process_args_and_render_json_obj(obj.update(**json_data))

    def patch(self, _id):
        obj = self._model_class_.get(_id, key=self._id_key_)
        json_data = g.json
        return process_args_and_render_json_obj(obj.update(**json_data))

    def delete(self, _id):
        obj = self._model_class_.get(_id, key=self._id_key_)
        obj.delete()
        return success_json()


def register_crud_api_view(view, bp_or_app, endpoint, url_slug):
    view_func = view.as_view(endpoint)
    bp_or_app.add_url_rule(
        '/%s/' % url_slug, defaults={'_id': None},
        view_func=view_func, methods=['GET', ])
    bp_or_app.add_url_rule(
        '/%s' % url_slug, view_func=view_func, methods=['POST', ])
    bp_or_app.add_url_rule(
        '/%s/<_id>' % url_slug, view_func=view_func,
        methods=['GET', 'PUT', 'PATCH', 'DELETE'])
