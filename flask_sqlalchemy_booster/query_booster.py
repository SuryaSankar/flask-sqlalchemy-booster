from flask_sqlalchemy import BaseQuery


class QueryBooster(BaseQuery):

    cls = None

    def desc(self, attr='id'):
        return self.order_by(getattr(self.model_class, attr).desc())

    def asc(self, attr='id'):
        return self.order_by(getattr(self.model_class, attr))
