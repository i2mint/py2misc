"""
Also posted on https://stackoverflow.com/questions/57596431/python-dict-like-interface-to-glom.
See there for possible comments.
"""
from collections.abc import Mapping
from glom import glom, Literal, Path, PathAccessError


# TODO: Handle names_of_literals concern better. Here affects all keys with that name (regardless of parent context)
class GlomMap(Mapping):
    """
    A dict-like interface to glom.
    Glom?
    https://glom.readthedocs.io/en/latest/

    >>> d = {
    ...     'a': 'simple',
    ...     'b': {'is': 'nested'},
    ...     'c': {'is': 'nested', 'and': 'has', 'a': [1, 2, 3]}
    ... }
    >>> g = GlomMap(d)
    >>>
    >>> assert list(g) == ['a', 'b.is', 'b', 'c.is', 'c.and', 'c.a', 'c']
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
                 target,
                 node_types=(dict,),
                 key_concat=lambda prefix, suffix: prefix + '.' + suffix,
                 names_of_literals=(),
                 **kwargs):
        __doc__ = "A Mapping interface for glom. Fixes the target, and keys are considered as keys\n\n" \
                  + str(glom.__doc__)
        self._target = target
        self._node_types = node_types
        self._key_concat = key_concat
        self._names_of_literals = set(names_of_literals)

        self._kwargs = kwargs  # the stuff that is given to the **kwargs of glom
        self._mk_similar_glommap = lambda x: self.__class__(x, key_concat=key_concat, node_types=node_types,
                                                            **kwargs)

    def __getitem__(self, spec):
        return glom(self._target, spec, **self._kwargs)

    def __len__(self):
        count = 0
        for _ in self:
            count += 1
        return count

    def __iter__(self):
        """Depth first traversal: All nodes yielded."""
        for k in self._target:
            val = self[Path(k)]
            if isinstance(self[k], *self._node_types):
                yield from (self._key_concat(k, nested_key) for nested_key in self._mk_similar_glommap(val))
            yield k


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
        for k in self._target:
            val = self[Path(k)]
            if isinstance(val, *self._node_types):
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


dot_str_key_iterator = lambda p: p.split('.')
bracket_getter = lambda obj, k: obj[k]


def simple_glom(target, spec,
                node_types=(dict,),
                key_iterator=dot_str_key_iterator,
                item_getter=bracket_getter
                ):
    for k in key_iterator(spec):
        print(k)
        target = item_getter(target, k)
        if not isinstance(target, node_types):
            break
    return target
