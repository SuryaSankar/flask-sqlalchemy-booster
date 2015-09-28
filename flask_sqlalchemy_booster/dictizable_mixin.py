"""DictizableMixin
A mixin class to add `todict` method to objects.

"""

from sqlalchemy.ext.associationproxy import AssociationProxy
from .utils import is_list_like, is_dict_like
from toolspy import deep_group
import json
from .json_encoder import json_encoder


def serialized_list(olist, rels_to_expand=[]):
    return map(
        lambda o: o.todict(
            rels_to_expand=rels_to_expand),
        olist)


class DictizableMixin(object):

    """Methods for converting Model instance to dict and json.

    Attributes:

        _attrs_to_serialize_ (list of str):  The columns which should
            be serialized as a part of the output dictionary

        _key_modifications_ (dict of str,str): A dictionary used to map
            the display names of columns whose original name we want
            to be modified in the json

        _rels_to_serialize_ (list of tuple of str):  A list of tuples. The
            first element of the tuple is the relationship
            that is to be serialized. The second element it the name of the
            attribute in the related model, the value of which is to be used
            as the representation

        _rels_to_expand_ (list of str): A list of relationships to expand.
            You can specify nested relationships by placing dots.

        _group_listrels_by_ (dict of str, list of str): A dictionary
            representing how to hierarchially group a list like relationship.
            The relationship fields are the keys and the list of the attributes
            based on which they are to be grouped are the values.


    """

    _attrs_to_serialize_ = []
    _key_modifications_ = {}
    _rels_to_serialize_ = []
    _rels_to_expand_ = []
    _group_listrels_by_ = {}

    @classmethod
    def is_list_attribute(cls, rel):
        if rel in cls.__mapper__.relationships:
            return cls.__mapper__.relationships[rel].uselist
        rel_instance = getattr(cls, rel)
        if isinstance(rel_instance, AssociationProxy):
            return cls.__mapper__.relationships[
                rel_instance.target_collection].uselist
        return False

    def to_serializable_dict(self, attrs_to_serialize=None,
                             rels_to_expand=None,
                             rels_to_serialize=None,
                             key_modifications=None):
        """
        An alias for `todict`
        """
        return self.todict(
            attrs_to_serialize=attrs_to_serialize,
            rels_to_expand=rels_to_expand, rels_to_serialize=rels_to_serialize,
            key_modifications=key_modifications)

    # Version 5.0
    def todict(self, attrs_to_serialize=None,
               rels_to_expand=None,
               rels_to_serialize=None,
               group_listrels_by=None,
               key_modifications=None):

        """Converts an instance to a dictionary form

        Args:


            attrs_to_serialize (list of str):  The columns which should
                be serialized as a part of the output dictionary

            key_modifications (dict of str,str): A dictionary used to map
                the display names of columns whose original name we want
                to be modified in the json

            rels_to_serialize (list of tuple of str):  A list of tuples. The
                first element of the tuple is the relationship
                that is to be serialized. The second element it the name of the
                attribute in the related model, the value of which is to be used
                as the representation

            rels_to_expand (list of str): A list of relationships to expand.
                You can specify nested relationships by placing dots.

            group_listrels_by (dict of str, list of str): A dictionary
                representing how to hierarchially group a list like relationship.
                The relationship fields are the keys and the list of the attributes
                based on which they are to be grouped are the values.


        """

        # Never replace the following code by the (attrs = attrs or
        # self._attrs_) idiom. Python considers empty list as false. So
        # even if you pass an empty list, it will take self._x_ value. But
        # we don't want that as the empty list is what we use to end
        # the recursion
        attrs_to_serialize = (
            self._attrs_to_serialize_ if attrs_to_serialize is None
            else attrs_to_serialize)
        rels_to_serialize = (
            self._rels_to_serialize_ if rels_to_serialize is None
            else rels_to_serialize)
        rels_to_expand = (
            self._rels_to_expand_ if rels_to_expand is None
            else rels_to_expand)
        key_modifications = (
            self._key_modifications_ if key_modifications is None
            else key_modifications)
        group_listrels_by = (
            self._group_listrels_by_ if group_listrels_by is None
            else group_listrels_by)
        # Convert rels_to_expand to a dictionary
        rels_to_expand_dict = {}
        for rel in rels_to_expand:
            partitioned_rels = rel.partition('.')
            if partitioned_rels[0] not in rels_to_expand_dict:
                rels_to_expand_dict[partitioned_rels[0]] = (
                    [partitioned_rels[-1]] if partitioned_rels[-1]
                    else [])
            else:
                if partitioned_rels[-1]:
                    rels_to_expand_dict[partitioned_rels[0]].append(
                        partitioned_rels[-1])

        # # Convert grouplistrelsby to a dict
        # group_listrels_dict = {}
        # for rel_to_group, grouping_keys in group_listrels_by.iteritems():
        #     partitioned_rel_to_group = rel_to_group.partition('.')
        #     if partitioned_rel_to_group[0] not in group_listrels_dict:
        #         group_listrels_dict[partitioned_rel_to_group[0]] = (
        #             {partitioned_rel_to_group[-1]: grouping_keys}
        #             if partitioned_rel_to_group[-1] else grouping_keys)
        #     else:
        #         if partitioned_rel_to_group[-1]:
        #             group_listrels_dict[
        #                 partitioned_rel_to_group[0]][
        #                     partitioned_rel_to_group[-1]] = grouping_keys

        # Serialize attrs
        result = self.serialize_attrs(*attrs_to_serialize)

        # Serialize rels
        if len(rels_to_serialize) > 0:
            for rel, id_attr in rels_to_serialize:
                rel_obj = getattr(self, rel) if hasattr(self, rel) else None
                if rel_obj is not None:
                    if is_list_like(rel_obj):
                        if (group_listrels_by is not None and
                                rel in group_listrels_by):
                            result[rel] = deep_group(
                                rel_obj,
                                attr_to_show=id_attr,
                                keys=group_listrels_by[rel]
                            )
                        else:
                            result[rel] = [getattr(item, id_attr)
                                           for item in rel_obj if hasattr(item, id_attr)]
                    elif is_dict_like(rel_obj):
                        result[rel] = {k: getattr(v, id_attr)
                                       for k, v in rel_obj.iteritems()
                                       if hasattr(v, id_attr)}
                    else:
                        result[rel] = getattr(rel_obj, id_attr) if hasattr(
                            rel_obj, id_attr) else None
                else:
                    result[rel] = None

        # Expand some rels
        for rel, child_rels in rels_to_expand_dict.iteritems():
            rel_obj = getattr(self, rel) if hasattr(self, rel) else None
            if rel_obj is not None:
                if is_list_like(rel_obj):
                    if (group_listrels_by is not None and
                            rel in group_listrels_by):
                        result[rel] = deep_group(
                            rel_obj,
                            keys=group_listrels_by[rel], serializer='todict',
                            serializer_kwargs={'rels_to_expand': child_rels}
                        )
                    else:
                        result[rel] = [i.todict(rels_to_expand=child_rels)
                                       if hasattr(i, 'todict') else i
                                       for i in rel_obj]
                        # result[rel] = serialized_list(
                        #     rel_obj, rels_to_expand=child_rels)
                elif is_dict_like(rel_obj):
                    result[rel] = {k: v.todict()
                                   if hasattr(v, 'todict') else v
                                   for k, v in rel_obj.iteritems()}
                else:
                    result[rel] = rel_obj.todict(
                        rels_to_expand=child_rels) if hasattr(
                        rel_obj, 'todict') else rel_obj

        for key, mod_key in key_modifications.items():
            if key in result:
                result[mod_key] = result.pop(key)

        return result

    def serialize_attrs(self, *args):
        """Converts and instance to a dictionary with only the specified
        attributes as keys

        Args:
            *args (list): The attributes to serialize

        Examples:

            >>> customer = Customer.create(name="James Bond", email="007@mi.com",
                                           phone="007", city="London")
            >>> customer.serialize_attrs('name', 'email')
            {'name': u'James Bond', 'email': u'007@mi.com'}

        """
        return dict([(a, getattr(self, a)) for a in args if hasattr(self, a)])

    def tojson(self, attrs_to_serialize=None,
               rels_to_expand=None,
               rels_to_serialize=None,
               key_modifications=None):
        return json.dumps(
            self.todict(
                attrs_to_serialize=attrs_to_serialize,
                rels_to_expand=rels_to_expand,
                rels_to_serialize=rels_to_serialize,
                key_modifications=key_modifications),
            default=json_encoder)
