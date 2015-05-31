"""
Borrows heavily from
https://github.com/mattupstate/overholt/blob/master/overholt/core.py

"""

from sqlalchemy import func
from toolspy import place_nulls, subdict, remove_and_mark_duplicate_dicts


class QueryableMixin(object):

    """
    Attributes
    ----------
    _no_overwrite_: list
                    The list of attributes that should not be overwritten

    """

    _no_overwrite_ = []

    def update(self, **kwargs):
        """Updates an instance

        Parameters
        ----------
        **kwargs: Arbitrary keyword arguments
                  Column names are keywords and their new values are the values

        >>> customer.update(email="newemail@x.com", name="new")
        """
        kwargs = self._preprocess_params(kwargs)
        for key, value in kwargs.iteritems():
            if key not in self._no_overwrite_:
                setattr(self, key, value)
        try:
            self.session.commit()
            return self
        except Exception as e:
            self.session.rollback()
            raise e

    def commit(self):
        self.session.commit()

    def save(self):
        """
        Saves a model instance to db

        >>> customer = Customer.new(name="hari")
        >>> customer.save()

        """
        self.session.add(self)
        self.session.commit()

    def delete(self, commit=True):
        self.session.delete(self)
        if commit:
            self.session.commit

    def _isinstance(self, model, raise_error=True):
        """Checks if the specified model instance matches the class model.
        By default this method will raise a `ValueError` if the model is not of
        expected type.

        Parameters
        ----------

        model: Class
        raise_error: boolean
        """
        rv = isinstance(model, self.__model__)
        if not rv and raise_error:
            raise ValueError('%s is not of type %s' % (model, self.__model__))
        return rv

    @classmethod
    def rollback_session(cls):
        cls.session.rollback()

    @classmethod
    def _preprocess_params(cls, kwargs):
        """Returns a preprocessed dictionary of parameters.
        Use this to filter the kwargs passed to `new`, `create`,
        `build` methods.

        Parameters
        -----------

        **kwargs: a dictionary of parameters
        """
        kwargs.pop('csrf_token', None)
        return kwargs

    @classmethod
    def filter_by(cls, **kwargs):
        """Same as SQLAlchemy's filter_by. Additionally this accepts
        two special keyword arguments `limit` and `reverse` for limiting
        the results and reversing the order respectively

        Parameters
        ----------

        **kwargs: filter parameters

        Examples
        --------
        >>> user = User.filter_by(email="new@x.com")

        >>> shipments = Shipment.filter_by(country="India", limit=3, reverse=True)

        """
        limit = kwargs.pop('limit', None)
        reverse = kwargs.pop('reverse', False)
        q = cls.query.filter_by(**kwargs)
        if reverse:
            q = q.order_by(cls.id.desc())
        if limit:
            q = q.limit(limit)
        return q

    @classmethod
    def filter(cls, *criterion, **kwargs):
        """Same as SQLAlchemy's filter_by. Additionally this accepts
        two special keyword arguments `limit` and `reverse` for limiting
        the results and reversing the order respectively

        Parameters
        ----------

        **kwargs: filter parameters

        Examples
        --------
        >>> user = User.filter(User.email=="new@x.com")

        >>> shipments = Order.filter(Order.price < 500, limit=3, reverse=True)

        """
        limit = kwargs.pop('limit', None)
        reverse = kwargs.pop('reverse', False)
        q = cls.query.filter_by(**kwargs).filter(*criterion)
        if reverse:
            q = q.order_by(cls.id.desc())
        if limit:
            q = q.limit(limit)
        return q

    @classmethod
    def count(cls, *criterion, **kwargs):
        """Returns a count of the instances meeting the specified
        filter criterion and kwargs

        Examples
        --------

        >>> User.count()
        500

        >>> User.count(country="India")
        300

        >>> User.count(User.age > 50, country="India")
        39

        """
        if criterion or kwargs:
            return cls.filter(
                *criterion,
                **kwargs).count()
        else:
            return cls.query.count()

    @classmethod
    def all(cls, *criterion, **kwargs):
        """Returns all the instances which fulfill the filtering
        criterion and kwargs if any given.

        Examples
        ---------

        >>> Tshirt.all()
        [tee1, tee2, tee4, tee5]

        >> Tshirt.all(reverse=True, limit=3)
        [tee5, tee4, tee2]

        >> Tshirt.all(color="Red")
        [tee4, tee2]
        """
        return cls.filter(*criterion, **kwargs).all()

    @classmethod
    def first(cls, *criterion, **kwargs):
        """Returns the first instance found of the service's model filtered by
        the specified key word arguments.

        :param **kwargs: filter parameters
        """
        return cls.filter(*criterion, **kwargs).first()

    @classmethod
    def one(cls, *criterion, **kwargs):
        return cls.filter(*criterion, **kwargs).one()

    @classmethod
    def last(cls, *criterion, **kwargs):
        kwargs['reverse'] = True
        return cls.first(*criterion, **kwargs)

    @classmethod
    def new(cls, **kwargs):
        """Returns a new, unsaved instance of the service's model class.

        :param **kwargs: instance parameters
        """
        return cls(**cls._preprocess_params(kwargs))

    @classmethod
    def add(cls, model, commit=True):
        if not isinstance(model, cls):
            raise ValueError('%s is not of type %s' (model, cls))
        cls.session.add(model)
        try:
            if commit:
                cls.session.commit()
            return model
        except:
            cls.session.rollback()
            raise

    @classmethod
    def add_all(cls, models, commit=True, check_type=False):
        if check_type:
            for model in models:
                if not isinstance(model, cls):
                    raise ValueError('%s is not of type %s' (model, cls))
        cls.session.add_all(models)
        try:
            if commit:
                cls.session.commit()
            return models
        except:
            cls.session.rollback()
            raise

    @classmethod
    def _get(cls, key, keyval, user_id=None):
        result = cls.query.filter(
            getattr(cls, key) == keyval)
        if user_id and hasattr(cls, 'user_id'):
            result = result.filter(cls.user_id == user_id)
        return result.one()

    @classmethod
    def get(cls, keyval, key='id', user_id=None):
        """Returns an instance of the service's model with the specified id.
        Returns `None` if an instance with the specified id does not exist.

        :param id: the instance id
        """
        if (key in cls.__table__.columns
                and cls.__table__.columns[key].primary_key):
            if user_id and hasattr(cls, 'user_id'):
                return cls.query.filter_by(id=keyval, user_id=user_id).one()
            return cls.query.get(keyval)
        else:
            result = cls.query.filter(
                getattr(cls, key) == keyval)
            if user_id and hasattr(cls, 'user_id'):
                result = result.filter(cls.user_id == user_id)
            return result.one()

    @classmethod
    def get_all(cls, keyvals, key='id', user_id=None):
        if len(keyvals) == 0:
            return []
        resultset = cls.query.filter(getattr(cls, key).in_(keyvals))
        if user_id and hasattr(cls, 'user_id'):
            resultset = resultset.filter(cls.user_id == user_id)
        # We need the results in the same order as the input keyvals
        # So order by field in SQL
        resultset = resultset.order_by(
            func.field(getattr(cls, key), *keyvals))
        return place_nulls(key, keyvals, resultset.all())

    # @classmethod
    # def get_all(cls, ids, user_id=None):
    #     return cls._get_all('id', ids, user_id=user_id)

    @classmethod
    def get_or_404(cls, id):
        """Returns an instance of the service's model with the specified id or
        raises an 404 error if an instance with the specified id does not exist

        :param id: the instance id
        """
        return cls.query.get_or_404(id)

    @classmethod
    def create(cls, **kwargs):
        """Returns a new, saved instance of the service's model class.

        :param **kwargs: instance parameters
        """
        try:
            return cls.add(cls.new(**kwargs))
        except:
            cls.session.rollback()
            raise

    @classmethod
    def find_or_create(cls, **kwargs):
        """Checks if an instance already exists in db with these kwargs else
        returns a new, saved instance of the service's model class.

        :param **kwargs: instance parameters
        """
        keys = kwargs.pop('keys') if 'keys' in kwargs else []
        return cls.first(**subdict(kwargs, keys)) or cls.create(**kwargs)

    @classmethod
    def update_or_create(cls, **kwargs):
        keys = kwargs.pop('keys') if 'keys' in kwargs else []
        obj = cls.first(**subdict(kwargs, keys))
        if obj is not None:
            for key, value in kwargs.iteritems():
                if (key not in keys and
                        key not in cls._no_overwrite_):
                    setattr(obj, key, value)
            try:
                cls.session.commit()
            except:
                cls.session.rollback()
                raise
        else:
            obj = cls.create(**kwargs)
        return obj

    @classmethod
    def create_all(cls, list_of_kwargs):
        try:
            return cls.add_all([
                cls.new(**kwargs) for kwargs in list_of_kwargs])
        except:
            cls.session.rollback()
            raise

    @classmethod
    def find_or_create_all(cls, list_of_kwargs, keys=[]):
        list_of_kwargs_wo_dupes, markers = remove_and_mark_duplicate_dicts(
            list_of_kwargs, keys)
        added_objs = cls.add_all([
            cls.first(**subdict(kwargs, keys)) or cls.new(**kwargs)
            for kwargs in list_of_kwargs_wo_dupes])
        result_objs = []
        iterator_of_added_objs = iter(added_objs)
        for idx in range(len(list_of_kwargs)):
            if idx in markers:
                result_objs.append(added_objs[markers[idx]])
            else:
                result_objs.append(next(
                    iterator_of_added_objs))
        return result_objs

    @classmethod
    def update_or_create_all(cls, list_of_kwargs, keys=[]):
        objs = []
        for kwargs in list_of_kwargs:
            obj = cls.first(**subdict(kwargs, keys))
            if obj is not None:
                for key, value in kwargs.iteritems():
                    if (key not in keys and
                            key not in cls._no_overwrite_):
                        setattr(obj, key, value)
            else:
                obj = cls.new(**kwargs)
            objs.append(obj)
        try:
            return cls.add_all(objs)
        except:
            cls.session.rollback()
            raise

    @classmethod
    def build(cls, **kwargs):
        """Returns a new, added but unsaved instance of the service's model class.

        :param **kwargs: instance parameters
        """
        return cls.add(cls.new(**kwargs), commit=False)

    @classmethod
    def find_or_build(cls, **kwargs):
        """Checks if an instance already exists in db with these kwargs else
        returns a new, saved instance of the service's model class.

        :param **kwargs: instance parameters
        """
        return cls.first(**kwargs) or cls.build(**kwargs)

    @classmethod
    def new_all(cls, list_of_kwargs):
        return [cls.new(**kwargs) for kwargs in list_of_kwargs]

    @classmethod
    def build_all(cls, list_of_kwargs):
        return cls.add_all([
            cls.new(**kwargs) for kwargs in list_of_kwargs], commit=False)

    @classmethod
    def find_or_build_all(cls, list_of_kwargs):
        return cls.add_all([cls.first(**kwargs) or cls.new(**kwargs)
                            for kwargs in list_of_kwargs], commit=False)

    @classmethod
    def update_all(cls, *criterion, **kwargs):
        try:
            r = cls.query.filter(*criterion).update(kwargs, 'fetch')
            cls.session.commit()
            return r
        except:
            cls.session.rollback()
            raise

    @classmethod
    def get_and_update(cls, id, **kwargs):
        """Returns an updated instance of the service's model class.

        :param model: the model to update
        :param **kwargs: update parameters
        """
        model = cls.get(id)
        for k, v in cls._preprocess_params(kwargs).items():
            setattr(model, k, v)
        cls.session.commit()
        return model

    @classmethod
    def get_and_setattr(cls, id, **kwargs):
        """Returns an updated instance of the service's model class.

        :param model: the model to update
        :param **kwargs: update parameters
        """
        model = cls.get(id)
        for k, v in cls._preprocess_params(kwargs).items():
            setattr(model, k, v)
        return model
