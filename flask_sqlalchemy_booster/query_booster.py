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

    def get(self, keyval, key='id'):
        if keyval is None:
            return None
        if key not in self.model_class.__table__.columns:
            raise Exception("Not a valid key")
        if self.model_class.__table__.columns[key].primary_key:
            try:
                self._get_existing_condition()
                return self.get(keyval)
            except:
                return self.filter(getattr(self.model_class, key) == keyval).first()
        else:
            return self.filter(getattr(self.model_class, key) == keyval).first()
