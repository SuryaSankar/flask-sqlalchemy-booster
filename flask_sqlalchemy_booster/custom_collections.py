from __future__ import absolute_import
from sqlalchemy.orm.collections import collection, _SerializableAttrGetter
from sqlalchemy import util, exc as sa_exc


class MappedDictOfLists(dict):

    def __init__(self, keyfunc):
        self.keyfunc = keyfunc

    @collection.appender
    @collection.internally_instrumented
    def append(self, value, _sa_initiator=None):
        key = self.keyfunc(value)
        if not self.__contains__(key):
            self.__setitem__(key, [], _sa_initiator)
        self.__getitem__(key).append(value)

    @collection.remover
    @collection.internally_instrumented
    def remove(self, value, _sa_initiator=None):
        """Remove an item by value, consulting the keyfunc for the key."""

        key = self.keyfunc(value)
        # Let self[key] raise if key is not in this collection
        # testlib.pragma exempt:__ne__
        if not self.__contains__(key) or value not in self[key]:
            raise sa_exc.InvalidRequestError(
                "Can not remove '%s': collection holds '%s' for key '%s'. "
                "Possible cause: is the MappedCollection key function "
                "based on mutable properties or properties that only obtain "
                "values after flush?" %
                (value, self[key], key))
        self.__getitem__(key, _sa_initiator).remove(value)

    @collection.converter
    def _convert(self, dictlike):
        """Validate and convert a dict-like object into values for set()ing.

        This is called behind the scenes when a MappedCollection is replaced
        entirely by another collection, as in::

          myobj.mappedcollection = {'a':obj1, 'b': obj2} # ...

        Raises a TypeError if the key in any (key, value) pair in the dictlike
        object does not match the key that this collection's keyfunc would
        have assigned for that value.

        """
        for incoming_key, valuelist in util.dictlike_iteritems(dictlike):
            for value in valuelist:
                new_key = self.keyfunc(value)
                if incoming_key != new_key:
                    raise TypeError(
                        "Found incompatible key %r for value %r; this "
                        "collection's "
                        "keying function requires a key of %r for this value." % (
                            incoming_key, value, new_key))
                yield value


def attribute_mapped_dict_of_lists(attr_name):
    getter = _SerializableAttrGetter(attr_name)
    return lambda: MappedDictOfLists(getter)
