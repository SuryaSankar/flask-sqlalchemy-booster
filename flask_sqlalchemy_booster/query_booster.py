from __future__ import absolute_import
from flask_sqlalchemy import BaseQuery, Pagination
from flask_sqlalchemy.model import DefaultMeta
from six.moves import range


class QueryBooster(BaseQuery):

    cls = None

    def __init__(self, *args, **kwargs):
        self.primary_entity = None
        self.model_class = None
        if len(args) > 0:
            self.primary_entity = args[0]
            if isinstance(self.primary_entity, DefaultMeta):
                self.model_class = self.primary_entity

        super(QueryBooster, self).__init__(*args, **kwargs)

    @property
    def mapper_model_class(self):
        # return self._primary_entity.mapper.class_
        return self.model_class

    def desc(self, attr=None):
        if attr is None:
            attr = self.model_class.primary_key_name()
        return self.order_by(getattr(self.model_class, attr).desc())

    def asc(self, attr=None):
        if attr is None:
            attr = self.model_class.primary_key_name()
        return self.order_by(getattr(self.model_class, attr))

    def last(self, *criterion, **kwargs):
        return self.filter_by(**kwargs).filter(*criterion).desc().first()

    def get_all(self, keyvals, key=None):
        if len(keyvals) == 0:
            return []
        if key is None:
            key = self.model_class.primary_key_name()
        original_keyvals = keyvals
        keyvals_set = list(set(keyvals))
        resultset = self.filter(getattr(self.model_class, key).in_(keyvals_set))
        key_result_mapping = {getattr(result, key): result for result in resultset.all()}
        return [key_result_mapping.get(kv) for kv in original_keyvals]

    # def get(self, keyval, key='id'):
    #     if keyval is None:
    #         return None
    #     if key not in self.model_class.__table__.columns:
    #         raise Exception("Not a valid key")
    #     if self.model_class.__table__.columns[key].primary_key:
    #         try:
    #             self._get_existing_condition()
    #             return self.get(keyval)
    #         except:
    #             return self.filter(getattr(self.model_class, key) == keyval).first()
    #     else:
    #         return self.filter(getattr(self.model_class, key) == keyval).first()

    def is_joined_with(self, model_class):
        return model_class in [entity.class_ for entity in self._join_entities]


    def buckets(self, bucket_size=None, offset_to_start_from=0, dont_apply_offsets_on_buckets=False):
        if dont_apply_offsets_on_buckets:
            items_count = self.count()
            while items_count > 0:
                items = self.limit(bucket_size).offset(offset_to_start_from).all()
                yield items
                items_count = self.count()
        else:
            items_count = self.offset(offset_to_start_from).count()
            no_of_buckets = items_count / bucket_size  + 1
            for bucket in range(no_of_buckets):
                items = self.limit(bucket_size).offset(offset_to_start_from + bucket*bucket_size).all()
                yield items

    def paginate(self, *args, **kwargs):
        pagination = super(QueryBooster, self).paginate(*args, **kwargs)
        distinct_total = self.order_by(None).distinct().count()
        items = self.distinct().limit(
            pagination.per_page).offset(
            (pagination.page - 1) * pagination.per_page
            ).all()
        return Pagination(
            self, pagination.page, pagination.per_page,
            distinct_total, items
        )
