from flask.views import MethodView
from .responses import process_args_and_render_json_list, process_args_and_render_json_obj, success_json

class CrudApiView(MethodView):

	_model_class_ = None
	_list_query_ = None
    _id_key_ = 'id'

	def get(self, _id):
		list_query = _list_query_ or _model_class_.query
		if _id is None:
			return process_args_and_render_json_list(_list_query_)
		else:
            return process_args_and_render_json_obj(_model_class_.get(_id, key=_id_key_))


    def post(self):
        json_data = g.json
        return process_args_and_render_json_obj(_model_class_.create(**json_data))

    def put(self, _id):
        obj = _model_class_.get(_id, key=_id_key_)
        json_data = g.json
        return process_args_and_render_json_obj(obj.update(**json_data))


    def patch(self, _id):
        obj = _model_class_.get(_id, key=_id_key_)
        json_data = g.json
        return process_args_and_render_json_obj(obj.update(**json_data))

    def delete(self, _id):
        obj = _model_class_.get(_id, key=_id_key_)
        obj.delete()
        return success_json()

    def register_at(self, bp_or_app, endpoint, url_slug):
        view = self.as_view(endpoint)
        bp_or_app.add_url_rule('/%s/' % url_slug, defaults={'_id': None}, view_func=view, methods=['GET',])
        bp_or_app.add_url_rule('/%s' % url_slug, view_func=view, methods=['POST',])
        bp_or_app.add_url_rule('/%s/<:_id>' % url_slug, view_func=view, methods=['GET', 'PUT', 'PATCH', 'DELETE'])

    # def register_category_api(
    #         merchandise_list_view, merchandise_instance_view, priceable_list_view):
    #     category = merchandise_instance_view._canvas_variant_class_.__mapper_args__[
    #         'polymorphic_identity']
    #     bp.add_url_rule('/%s_merchandise' % category, methods=['GET'],
    #                     view_func=merchandise_list_view.as_view('list_%s_merchandise' % category))
    #     # bp.add_url_rule('/%s_merchandise' % category, methods=['POST'],
    #     #                 view_func=merchandise_instance_view.as_view(
    #     #                     'create_%s_merchandise' % category))
    #     bp.add_url_rule('/%s/canvases/<canvas_id>/merchandise' % category, methods=['POST'],
    #                     view_func=merchandise_instance_view.as_view(
    #                         'create_%s_merchandise' % category))
    #     bp.add_url_rule('/%s_merchandise/<label_or_id>' % category, methods=['PUT', 'PATCH'],
    #                     view_func=merchandise_instance_view.as_view(
    #                         'update_%s_merchandise' % category))
    #     bp.add_url_rule('/%s/canvases/<canvas_id>/priceables' % category, methods=['GET'],
    #                     view_func=priceable_list_view.as_view(
    #                         'list_%s_priceables' % category))