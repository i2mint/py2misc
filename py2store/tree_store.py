"""
Also posted on https://stackoverflow.com/questions/57596431/python-dict-like-interface-to-glom.
See there for possible comments.
"""
from collections.abc import Mapping, Collection

# from glom import glom, Literal, Path, PathAccessError


dot_str_key_iterator = lambda p: p.split('.')
bracket_getter = lambda obj, k: obj[k]


def bracket_or_attribute(obj, k):
    try:
        return obj[k]
    except Exception:
        return getattr(obj, k)


def mk_is_branch_func_from_types(*branch_types):
    assert all(isinstance(x, type) for x in branch_types), "branch_types must all be types"

    def is_branch(node_val):
        return isinstance(node_val, branch_types)

    return is_branch


class NodeGetter:
    """
    A accessing nested (i.e. tree-like) data as data['a', 'b', 'c'] instead of data['a']['b']['c']
    This is the base to be able to define other path-based ways to see nested data.
    For example:
        data['a.b.c'.split('.')]


    >>> d = {
    ...     'a': 'simple',
    ...     'b': {'is': 'nested'},
    ...     'c': {'is': 'nested', 'and': 'has', 'a': [1, 2, 3]}
    ... }
    >>> g = NodeGetter(d)
    >>>
    >>> assert g['a'] == 'simple'
    >>> assert g['b', 'is'] == 'nested'
    >>> assert g['c', 'a'] == [1, 2, 3]
    >>> assert g['c', 'a', 1] == 2
    >>>
    >>> assert d['c']['a'][1] == 2  # it's to avoid accessing it this way.
    >>> # But can also expand on this and do things like:
    >>> assert g['b.is'.split('.')] == 'nested'
    >>> assert g['c/a'.split('/')] == [1, 2, 3]
    >>> # ... or subclass/wrap NodeGetter to do it automatically, given a protocol
    >>>
    >>> def int_if_possible(x):
    ...     try:
    ...         return int(x)
    ...     except ValueError:
    ...         return x
    >>> p = lambda k: map(int_if_possible, k.split('.'))
    >>> assert g[p('c.a.1')] == 2
    """
    def __init__(self, source, item_getter=bracket_or_attribute):
        self._source = source
        self._item_getter = item_getter

    def __getitem__(self, path):
        __source = self._source
        for k in path:
            try:
                __source = self._item_getter(__source, k)
            except Exception as e:
                raise KeyError(f"Accessing {path} produced an error: {e}")
        return __source


class TreeMap(NodeGetter, Mapping):
    """
    A dict-like interface to any nested structure.

    >>> d = {
    ...     'a': 'simple',
    ...     'b': {'is': 'nested'},
    ...     'c': {'is': 'nested', 'and': 'has', 'a': [1, 2, 3]}
    ... }
    >>> g = TreeMap(d)
    >>>
    >>> assert list(g) == ['a', ['b', 'is'], 'b', ['c', 'is'], ['c', 'and'], ['c', 'a'], 'c']
    >>> assert g['a'] == 'simple'
    >>> assert g['b', 'is'] == 'nested'
    >>> assert g['c', 'a'] == [1, 2, 3]
    >>> assert g['c', 'a', 1] == 2
    >>>
    >>> for k, v in g.items():
    ...     print(f"{k}: {v}")
    a: simple
    ['b', 'is']: nested
    b: {'is': 'nested'}
    ['c', 'is']: nested
    ['c', 'and']: has
    ['c', 'a']: [1, 2, 3]
    c: {'is': 'nested', 'and': 'has', 'a': [1, 2, 3]}
    >>> assert len(g) == len(list(g))
    """

    def __init__(self,
                 source,
                 is_branch=None,
                 item_getter=bracket_or_attribute):
        __doc__ = "A collection.abc.Mapping interface to any object"
        NodeGetter.__init__(self, source, item_getter=item_getter)
        self._source = source
        self._is_branch = is_branch or mk_is_branch_func_from_types(*(type(self._source),))

        self._mk_similar_treemap = lambda x: self.__class__(x, is_branch=is_branch, item_getter=item_getter)


    def __len__(self):
        c = 0
        for k in self._source:
            val = self._source[k]
            if self._is_branch(val):
                c += len(self._mk_similar_treemap(val))
            c += 1
        return c

    def __iter__(self):
        """Depth first traversal: All nodes yielded."""
        for k in self._source:
            val = self._source[k]
            if self._is_branch(val):
                yield from ([k] + [nested_key] for nested_key in self._mk_similar_treemap(val))
            yield k


# TODO: Handle names_of_literals concern better. Here affects all keys with that name (regardless of parent context)
class GlomMap(Mapping):
    """
    A dict-like interface to any nested structure.

    >>> d = {
    ...     'a': 'simple',
    ...     'b': {'is': 'nested'},
    ...     'c': {'is': 'nested', 'and': 'has', 'a': [1, 2, 3]}
    ... }
    >>> g = GlomMap(d)
    >>>
    >>> assert list(g) == ['a', 'b.is', 'b', 'c.is', 'c.and', 'c.a', 'c']
    >>> assert len(g) == 7
    >>> assert g['a'] == 'simple'
    >>> assert g['b.is'] == 'nested'
    >>> assert g['c.a'] == [1, 2, 3]
    >>>
    >>> for k, v in g.items():
    ...     print(f"{k}: {v}")
    ...
    a: simple
    b.is: nested
    b: {'is': 'nested'}
    c.is: nested
    c.and: has
    c.a: [1, 2, 3]
    c: {'is': 'nested', 'and': 'has', 'a': [1, 2, 3]}
    """

    def __init__(self,
                 source,
                 node_types=None,
                 keys_of_path=dot_str_key_iterator,
                 item_getter=bracket_getter,
                 key_concat=lambda prefix, suffix: prefix + '.' + suffix
                 ):
        __doc__ = "A collection.abc.Mapping interface to any object"
        self._source = source
        if node_types is None:
            node_types = (type(self._source),)
        # self._node_types = node_types
        self._is_branch = mk_is_branch_func_from_types(*node_types)
        self._keys_of_path = keys_of_path
        self._item_getter = item_getter
        self._key_concat = key_concat

        self._mk_similar_glommap = lambda x: self.__class__(x, key_concat=key_concat, node_types=node_types)

    def __getitem__(self, path):
        # return glom(self._source, spec, **self._kwargs)
        source = self._source
        for k in self._keys_of_path(path):
            source = self._item_getter(source, k)
            if not self._is_branch(source):
                break
        return source

    def __len__(self):
        count = 0
        for _ in self:
            count += 1
        return count

    def __iter__(self):
        """Depth first traversal: All nodes yielded."""
        for k in self._source:
            val = self[k]
            if self._is_branch(val):
                yield from (self._key_concat(k, nested_key) for nested_key in self._mk_similar_glommap(val))
            yield k
            #
            # if not self._is_branch(val):
            #     yield k
            # else:
            #     if self.
            # if self._is_branch(val):
            #     yield from (self._key_concat(k, nested_key) for nested_key in self._mk_similar_glommap(val))
            # if self._leafs_only
            #     was_branch = True
            # if self._leafs_only:
            #     yield k


class GlomLeafMap(GlomMap):
    """
    A dict-like interface to glom. Here, only leaf keys are taken into account.

    >>> d = {
    ...     'a': 'simple',
    ...     'b': {'is': 'nested'},
    ...     'c': {'is': 'nested', 'and': 'has', 'a': [1, 2, 3]}
    ... }
    >>> g = GlomLeafMap(d)
    >>>
    >>> assert list(g) == ['a', 'b.is', 'c.is', 'c.and', 'c.a']
    >>> assert(len(g)) == 5
    >>> assert g['a'] == 'simple'
    >>> assert g['b.is'] == 'nested'
    >>> assert g['c.a'] == [1, 2, 3]
    >>>
    >>> for k, v in g.items():
    ...     print(f"{k}: {v}")
    ...
    a: simple
    b.is: nested
    c.is: nested
    c.and: has
    c.a: [1, 2, 3]
    """

    def __iter__(self):
        """Depth first traversal: Only leaf nodes yielded."""
        for k in self._source:
            val = self[k]
            if self._is_branch(val):
                yield from (self._key_concat(k, nested_key) for nested_key in self._mk_similar_glommap(val))
            else:
                yield k

            # if isinstance(self[k], *self._node_types):
            #     try:
            #         yield from (self._key_concat(k, nested_key) for nested_key in self._mk_similar_glommap(self[k]))
            #     except PathAccessError:
            #         path_k = Path(k)
            #         yield from (self._key_concat(k, nested_key) for nested_key in
            #                     self._mk_similar_glommap(self[path_k]))
            # else:
            #     yield k


def simple_glom(source, path,
                is_branch=None,
                key_iterator=dot_str_key_iterator,
                item_getter=bracket_getter
                ):
    """

    Args:
        source: nested structure
        path: what you want to extract from the nested structure
        node_types: The node
        key_iterator:
        item_getter:

    Returns: The value of the node of source specified by node path

    >>> class MyMap:
    ...     def __init__(self, d):
    ...         self.d = d
    ...     def __getitem__(self, k):
    ...         v = self.d[k]
    ...         if isinstance(v, (dict, MyMap)):
    ...             return MyMap(v)
    ...         else:
    ...             return v
    >>> MyMap.__getitem__.__doc__ = 'just delegating'
    >>>
    >>> m = MyMap({'a': {'b': {'c': 'd'}}})
    >>> m['a']['b']['c']  # see that m acts like a dict
    'd'
    >>>
    >>> m = MyMap({'a': {'b': {'c': 'd'}}})
    >>> simple_glom(m, 'a.b.c')  # see that you can use paths as keys
    'd'
    >>> # Access a class with a /-separated path of it's methods. Crazy huh?
    >>> from types import FunctionType
    >>> from functools import partial
    >>> attr_glom = partial(simple_glom,
    ...                     key_iterator=lambda p: p.split('/'),
    ...                     is_branch=mk_is_branch_func_from_types(FunctionType, type),
    ...                     item_getter=getattr)
    >>> assert attr_glom(MyMap, '__getitem__/__doc__') == 'just delegating'
    >>>
    """
    is_branch = is_branch or mk_is_branch_func_from_types(type(source))
    for k in key_iterator(path):
        source = item_getter(source, k)
        if not is_branch(source):
            break
    return source
