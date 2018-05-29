from flask_sqlalchemy import BaseQuery


class QueryBooster(BaseQuery):

    cls = None

    def desc(self, attr='id'):
        return self.order_by(getattr(self.model_class, attr).desc())

    def asc(self, attr='id'):
        return self.order_by(getattr(self.model_class, attr))

    def last(self, *criterion, **kwargs):
        return self.filter_by(**kwargs).filter(*criterion).desc().first()

    def get_all(self, keyvals, key='id'):
        if len(keyvals) == 0:
            return []
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


    def buckets(self, bucket_size=None, offset_every_bucket=True):
        items_count = self.count()
        if offset_every_bucket:
            no_of_buckets = items_count / bucket_size  + 1
            for bucket in range(no_of_buckets):
                items = self.limit(bucket_size).offset(bucket*bucket_size).all()
                yield items
        else:
            while items_count > 0:
                items = self.limit(bucket_size).all()
                yield items
                items_count = self.count()