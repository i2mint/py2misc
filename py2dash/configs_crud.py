import re

import anymarkup  # TODO: Avoid dependency when possible?

from py2store.stores.local_store import RelativePathFormatStoreEnforcingFormat as LocalFileStore


class ConfigStore(LocalFileStore):
    def _obj_of_data(self, data):
        return anymarkup.parse(data)

    def _data_of_obj(self, obj):
        # format = obj['_format']
        # del obj['_format']
        # Note: The two lines above can be replaced by expression below:
        data_format = obj.pop('_format')
        return anymarkup.serialize(obj, data_format).decode("utf-8")


class KeyToName:
    """key_to_name function makers"""

    @staticmethod
    def by_sink_character_replacement(repl_non_alphanum_with='__'):
        non_alpha_num = re.compile('\W')
        non_letter_or_underscore = re.compile('^[^a-zA-Z_]+')

        def key_to_name(k):
            k = non_alpha_num.sub(repl_non_alphanum_with, k)
            k = non_letter_or_underscore.sub('', k)  # Remove leading non-letter and non-underscore characters
            return k

        return key_to_name

    @staticmethod
    def from_mapping(name_of_key, default_key_to_name_func=None, raise_if_missing_key=True):
        def key_to_name(k):
            if k in name_of_key:
                return name_of_key[k]
            elif callable(default_key_to_name_func):
                return default_key_to_name_func(k)
            elif raise_if_missing_key:
                raise KeyError(f"Key not found in name_of_key map: {k}")
            else:
                pass

        return key_to_name


DFLT_KEY_TO_NAME = KeyToName.by_sink_character_replacement(repl_non_alphanum_with='__')
from inspect import Parameter, Signature


def mapping_to_signature(d):
    params = [Parameter(name=k, kind=Parameter.KEYWORD_ONLY, default=v) for k, v in d.items()]
    return Signature(parameters=params)


def key_to_edit_func(store, key, key_to_name=DFLT_KEY_TO_NAME):
    """
    Make a function to save data under store[key], whose signature reflects the already stored (nested) data.

    >>> from inspect import signature
    >>> from py2misc.py2dash.configs_crud import key_to_edit_func
    >>>
    >>> store = {
    ...     'thing_one': {'a': 1, 'b': 'one'},
    ...     'thing_two': {'c': 2, 'd': 'two', 'e': {'foo': 'bar', 'hello': [1, 2, 3]}},
    ... }
    >>>
    >>> funcs = [key_to_edit_func(store, key) for key in store]
    >>> for func in funcs:
    ...     print(f"{func.__name__}: {signature(func)}")
    thing_one: (*, a=1, b='one')
    thing_two: (*, c=2, d='two', e={'foo': 'bar', 'hello': [1, 2, 3]})
    >>>
    >>> func = funcs[0]
    >>> func(b='world')
    >>> store  # see that store['thing_one']['b'] is updated
    {'thing_one': {'a': 1, 'b': 'world'}, 'thing_two': {'c': 2, 'd': 'two', 'e': {'foo': 'bar', 'hello': [1, 2, 3]}}}
    >>>
    >>> # but...
    >>> signature(func)  # see that signature of func hasn't changed (not what we want!)
    <Signature (*, a=1, b='one')>
    """

    # The following function just takes all input key-val pairs and save them to the store under key
    def edit_func(**kwargs):  # here, just define what the function should do
        store[key].update(kwargs)

    edit_func.__qualname__ = edit_func.__name__ = key_to_name(key)  # give the function the desired name
    edit_func.__signature__ = mapping_to_signature(store[key])  # give the function the desired signature

    return edit_func

    # Explanation of signature steps:
    # We need to have a signature for the edit_func, along with defaults...
    # val = store[key]  # so we look at the val under the key (this val is supposed to be a mapping itself)
    # sig = mapping_to_signature(val)  # make a function signature from it
    # edit_func.__signature__ = sig  # and tell the function that's it's signature
