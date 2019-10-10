from py2store.base import Persister, static_identity_method, Item, Key, Val, no_such_item, KeyIter


class Store(Persister):
    """
    By store we mean key-value store. This could be files in a filesystem, objects in s3, or a database. Where and
    how the content is stored should be specified, but StoreInterface offers a dict-like interface to this.

    __getitem__ calls: _id_of_key			                    _obj_of_data
    __setitem__ calls: _id_of_key		        _data_of_obj
    __delitem__ calls: _id_of_key
    __iter__    calls:	            _key_of_id

    >>> # Default store: no key or value conversion ################################################
    >>> s = Store()
    >>> s['foo'] = 33
    >>> s['bar'] = 65
    >>> assert list(s.items()) == [('foo', 33), ('bar', 65)]
    >>> assert list(s.store.items()) == [('foo', 33), ('bar', 65)]  # see that the store contains the same thing
    >>>
    >>> ################################################################################################
    >>> # Now let's make stores that have a key and value conversion layer #############################
    >>> # input keys will be upper cased, and output keys lower cased ##################################
    >>> # input values (assumed int) will be converted to ascii string, and visa versa #################
    >>> ################################################################################################
    >>>
    >>> def test_store(s):
    ...     s['foo'] = 33  # write 33 to 'foo'
    ...     assert 'foo' in s  # __contains__ works
    ...     assert 'no_such_key' not in s  # __nin__ works
    ...     s['bar'] = 65  # write 65 to 'bar'
    ...     assert len(s) == 2  # there are indeed two elements
    ...     assert list(s) == ['foo', 'bar']  # these are the keys
    ...     assert list(s.keys()) == ['foo', 'bar']  # the keys() method works!
    ...     assert list(s.values()) == [33, 65]  # the values() method works!
    ...     assert list(s.items()) == [('foo', 33), ('bar', 65)]  # these are the items
    ...     assert list(s.store.items()) == [('FOO', '!'), ('BAR', 'A')]  # but note the internal representation
    ...     assert s.get('foo') == 33  # the get method works
    ...     assert s.get('no_such_key', 'something') == 'something'  # return a default value
    ...     del(s['foo'])  # you can delete an item given its key
    ...     assert len(s) == 1  # see, only one item left!
    ...     assert list(s.items()) == [('bar', 65)]  # here it is
    >>>
    >>> # We can introduce this conversion layer in several ways. Here's a few... ######################
    >>> # by subclassing ###############################################################################
    >>> class MyStore(Store):
    ...     def _id_of_key(self, k):
    ...         return k.upper()
    ...     def _key_of_id(self, _id):
    ...         return _id.lower()
    ...     def _data_of_obj(self, obj):
    ...         return chr(obj)
    ...     def _obj_of_data(self, data):
    ...         return ord(data)
    >>> s = MyStore(store=dict())  # note that you don't need to specify dict(), since it's the default
    >>> test_store(s)
    >>>
    >>> # by assigning functions to converters ##########################################################
    >>> class MyStore(Store):
    ...     def __init__(self, store, _id_of_key, _key_of_id, _data_of_obj, _obj_of_data):
    ...         super().__init__(store)
    ...         self._id_of_key = _id_of_key
    ...         self._key_of_id = _key_of_id
    ...         self._data_of_obj = _data_of_obj
    ...         self._obj_of_data = _obj_of_data
    ...
    >>> s = MyStore(dict(),
    ...             _id_of_key=lambda k: k.upper(),
    ...             _key_of_id=lambda _id: _id.lower(),
    ...             _data_of_obj=lambda obj: chr(obj),
    ...             _obj_of_data=lambda data: ord(data))
    >>> test_store(s)
    >>>
    >>> # using a Mixin class #############################################################################
    >>> class Mixin:
    ...     def _id_of_key(self, k):
    ...         return k.upper()
    ...     def _key_of_id(self, _id):
    ...         return _id.lower()
    ...     def _data_of_obj(self, obj):
    ...         return chr(obj)
    ...     def _obj_of_data(self, data):
    ...         return ord(data)
    ...
    >>> class MyStore(Mixin, Store):  # note that the Mixin must come before Store in the mro
    ...     pass
    ...
    >>> s = MyStore()  # no dict()? No, because default anyway
    >>> test_store(s)
    >>>
    >>> # adding wrapper methods to an already made Store instance #########################################
    >>> s = Store(dict())
    >>> s._id_of_key=lambda k: k.upper()
    >>> s._key_of_id=lambda _id: _id.lower()
    >>> s._data_of_obj=lambda obj: chr(obj)
    >>> s._obj_of_data=lambda data: ord(data)
    >>> test_store(s)
    """

    # __slots__ = ('_id_of_key', '_key_of_id', '_data_of_obj', '_obj_of_data')

    def __init__(self, store=dict):
        if isinstance(store, type):
            store = store()
        self.store = store

    _id_of_key = static_identity_method
    _key_of_id = static_identity_method
    _data_of_obj = static_identity_method
    _obj_of_data = static_identity_method

    # Read ####################################################################
    def __getitem__(self, k: Key) -> Val:
        return self._obj_of_data(self.store.__getitem__(self._id_of_key(k)))

    def get(self, k: Key, default=None) -> Val:
        data = self.store.get(self._id_of_key(k), no_such_item)
        if data is not no_such_item:
            return self._obj_of_data(data)
        else:
            return default

    # Explore ####################################################################
    def __iter__(self) -> KeyIter:
        return map(self._key_of_id, self.store.__iter__())

    def __len__(self) -> int:
        return self.store.__len__()

    def __contains__(self, k) -> bool:
        return self.store.__contains__(self._id_of_key(k))

    def head(self) -> Item:
        for k, v in self.items():
            return k, v

    # Write ####################################################################
    def __setitem__(self, k: Key, v: Val):
        return self.store.__setitem__(self._id_of_key(k), self._data_of_obj(v))

    # Delete ####################################################################
    def __delitem__(self, k: Key):
        return self.store.__delitem__(self._id_of_key(k))

    def clear(self):
        raise NotImplementedError('''
        The clear method was overridden to make dangerous difficult.
        If you really want to delete all your data, you can do so by doing:
            try:
                while True:
                    self.popitem()
            except KeyError:
                pass''')

    # Misc ####################################################################
    def __repr__(self):
        return self.store.__repr__()


class StoreLessDunders(Persister):
    """

    Same as Store above, but where some of the dunder references in the code were replaced by functions themselves.
    This what suggested by Martijn Pieters (no sure why, again).
    doctests pass, but don't see a significant or consistent improvement in speed

    self._obj_of_data(self.store.__getitem__(self._id_of_key(k)))
    --> self._obj_of_data(self.store[self._id_of_key(k)])

    map(self._key_of_id, self.store.__iter__())
    --> map(self._key_of_id, iter(self.store))

    self.store.__len__()
    --> len(self.store)

    self.store.__contains__(self._id_of_key(k))
    --> self._id_of_key(k) in self.store

    self.store.__setitem__(self._id_of_key(k), self._data_of_obj(v))
    --> self.store[self._id_of_key(k)] = self._data_of_obj(v)
    # Note that there's a difference here, since in the old way, a value COULD be returned (if __setitem__ did)

    self.store.__delitem__(self._id_of_key(k))
    --> del self.store[self._id_of_key(k)]
    # Same comment about no return value for __setitem__

    self.store.__repr__()
    --> repr(self.store)


    >>> Store = StoreLessDunders
    >>> # Default store: no key or value conversion ################################################
    >>> s = Store()
    >>> s['foo'] = 33
    >>> s['bar'] = 65
    >>> assert list(s.items()) == [('foo', 33), ('bar', 65)]
    >>> assert list(s.store.items()) == [('foo', 33), ('bar', 65)]  # see that the store contains the same thing
    >>>
    >>> ################################################################################################
    >>> # Now let's make stores that have a key and value conversion layer #############################
    >>> # input keys will be upper cased, and output keys lower cased ##################################
    >>> # input values (assumed int) will be converted to ascii string, and visa versa #################
    >>> ################################################################################################
    >>>
    >>> def test_store(s):
    ...     s['foo'] = 33  # write 33 to 'foo'
    ...     assert 'foo' in s  # __contains__ works
    ...     assert 'no_such_key' not in s  # __nin__ works
    ...     s['bar'] = 65  # write 65 to 'bar'
    ...     assert len(s) == 2  # there are indeed two elements
    ...     assert list(s) == ['foo', 'bar']  # these are the keys
    ...     assert list(s.keys()) == ['foo', 'bar']  # the keys() method works!
    ...     assert list(s.values()) == [33, 65]  # the values() method works!
    ...     assert list(s.items()) == [('foo', 33), ('bar', 65)]  # these are the items
    ...     assert list(s.store.items()) == [('FOO', '!'), ('BAR', 'A')]  # but note the internal representation
    ...     assert s.get('foo') == 33  # the get method works
    ...     assert s.get('no_such_key', 'something') == 'something'  # return a default value
    ...     del(s['foo'])  # you can delete an item given its key
    ...     assert len(s) == 1  # see, only one item left!
    ...     assert list(s.items()) == [('bar', 65)]  # here it is
    >>>
    >>> # We can introduce this conversion layer in several ways. Here's a few... ######################
    >>> # by subclassing ###############################################################################
    >>> class MyStore(Store):
    ...     def _id_of_key(self, k):
    ...         return k.upper()
    ...     def _key_of_id(self, _id):
    ...         return _id.lower()
    ...     def _data_of_obj(self, obj):
    ...         return chr(obj)
    ...     def _obj_of_data(self, data):
    ...         return ord(data)
    >>> s = MyStore(store=dict())  # note that you don't need to specify dict(), since it's the default
    >>> test_store(s)
    >>>
    >>> # by assigning functions to converters ##########################################################
    >>> class MyStore(Store):
    ...     def __init__(self, store, _id_of_key, _key_of_id, _data_of_obj, _obj_of_data):
    ...         super().__init__(store)
    ...         self._id_of_key = _id_of_key
    ...         self._key_of_id = _key_of_id
    ...         self._data_of_obj = _data_of_obj
    ...         self._obj_of_data = _obj_of_data
    ...
    >>> s = MyStore(dict(),
    ...             _id_of_key=lambda k: k.upper(),
    ...             _key_of_id=lambda _id: _id.lower(),
    ...             _data_of_obj=lambda obj: chr(obj),
    ...             _obj_of_data=lambda data: ord(data))
    >>> test_store(s)
    >>>
    >>> # using a Mixin class #############################################################################
    >>> class Mixin:
    ...     def _id_of_key(self, k):
    ...         return k.upper()
    ...     def _key_of_id(self, _id):
    ...         return _id.lower()
    ...     def _data_of_obj(self, obj):
    ...         return chr(obj)
    ...     def _obj_of_data(self, data):
    ...         return ord(data)
    ...
    >>> class MyStore(Mixin, Store):  # note that the Mixin must come before Store in the mro
    ...     pass
    ...
    >>> s = MyStore()  # no dict()? No, because default anyway
    >>> test_store(s)
    >>>
    >>> # adding wrapper methods to an already made Store instance #########################################
    >>> s = Store(dict())
    >>> s._id_of_key=lambda k: k.upper()
    >>> s._key_of_id=lambda _id: _id.lower()
    >>> s._data_of_obj=lambda obj: chr(obj)
    >>> s._obj_of_data=lambda data: ord(data)
    >>> test_store(s)
    """

    # __slots__ = ('_id_of_key', '_key_of_id', '_data_of_obj', '_obj_of_data')

    def __init__(self, store=dict):
        if isinstance(store, type):
            store = store()
        self.store = store

    _id_of_key = static_identity_method
    _key_of_id = static_identity_method
    _data_of_obj = static_identity_method
    _obj_of_data = static_identity_method

    # Read ####################################################################
    def __getitem__(self, k: Key) -> Val:
        return self._obj_of_data(self.store[self._id_of_key(k)])

    def get(self, k: Key, default=None) -> Val:
        data = self.store.get(self._id_of_key(k), no_such_item)
        if data is not no_such_item:
            return self._obj_of_data(data)
        else:
            return default

    # Explore ####################################################################
    def __iter__(self) -> KeyIter:
        return map(self._key_of_id, iter(self.store))

    def __len__(self) -> int:
        return len(self.store)

    def __contains__(self, k) -> bool:
        return self._id_of_key(k) in self.store

    def head(self) -> Item:
        for k, v in self.items():
            return k, v

    # Write ####################################################################
    def __setitem__(self, k: Key, v: Val):
        self.store[self._id_of_key(k)] = self._data_of_obj(v)
        # return self.store.__setitem__(self._id_of_key(k), self._data_of_obj(v))

    # Delete ####################################################################
    def __delitem__(self, k: Key):
        del self.store[self._id_of_key(k)]
        # return self.store.__delitem__(self._id_of_key(k))

    def clear(self):
        raise NotImplementedError('''
        The clear method was overridden to make dangerous difficult.
        If you really want to delete all your data, you can do so by doing:
            try:
                while True:
                    self.popitem()
            except KeyError:
                pass''')

    # Misc ####################################################################
    def __repr__(self):
        return repr(self.store)
