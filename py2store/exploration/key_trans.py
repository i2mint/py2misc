import os
from functools import wraps
from py2store.key_mappers.naming import StrTupleDict
from py2store.trans import wrap_kvs

pjoin = os.path.join


def mk_tupled_store_from_path_format_store_cls(store, subpath='', store_cls_kwargs=None,
                                               keymap=StrTupleDict, keymap_kwargs=None,
                                               name=None):
    """Wrap a store (instance or class) that uses string keys to make it into a store that uses tuple keys.

    Args:
        store: The instance or class to wrap
        subpath: The subpath (defining the subset of the data pointed at by the URI
        store_cls_kwargs:  # if store is a class, the kwargs that you would have given the store_cls to make itself
        keymap:  # the keymap instance or class you want to use to map keys
        keymap_kwargs:  # if keymap is a cls, the kwargs to give it (besides the subpath)
        name: The name to give the class the function will make here

    Returns: An instance of a wrapped class


    Example:
    ```
    # Get a (sessiono,bt) indexed LocalJsonStore
    s = mk_tupled_store_from_path_format_store_cls(LocalJsonStore,
                                                   os.path.join(root_dir, 'd'),
                                                   subpath='{session}/d/{bt}',
                                                   keymap_kwargs=dict(process_info_dict={'session': int, 'bt': int}))
    ```

    """
    if isinstance(keymap, type):
        keymap = keymap(subpath, **(keymap_kwargs or {}))  # make the keymap instance

    if isinstance(store, type):
        name = name or 'Str2TupleWrapped' + store.__name__
        _WrappedStoreCls = wrap_kvs(store, name=name,
                                    key_of_id=keymap.str_to_tuple, id_of_key=keymap.tuple_to_str)

        class WrappedStoreCls(_WrappedStoreCls):
            def __init__(self, root_uri):
                path_format = pjoin(root_uri, subpath)
                super().__init__(path_format, **(store_cls_kwargs or {}))

        return WrappedStoreCls
    else:
        name = name or 'Str2TupleWrapped' + store.__class__.__name__
        return wrap_kvs(store, name=name, key_of_id=keymap.str_to_tuple, id_of_key=keymap.tuple_to_str)
