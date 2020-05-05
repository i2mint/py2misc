from py2store import kv_wrap


# from py2store.utils.explicit import ExplicitKeysSource


def mk_explicit_key_map_trans(key_of_id_map=None, id_of_key_map=None):
    if key_of_id_map is None:
        assert hasattr(id_of_key_map, 'items')
        key_of_id_map = {v: k for k, v in id_of_key_map.items()}
    elif id_of_key_map is None:
        assert hasattr(key_of_id_map, 'items')
        id_of_key_map = {v: k for k, v in key_of_id_map.items()}

    class ExplicitKeyMap:
        key_of_id = key_of_id_map
        id_of_key = id_of_key_map

        def _key_of_id(self, _id):
            return self.key_of_id[_id]

        def _id_of_key(self, k):
            return self.id_of_key[k]

    return ExplicitKeyMap()


id_of_key_map = {'mykey': 'the_real_key', 'my_other_key': 'some_complicated_key'}
StoreYourWrapping = None
S = kv_wrap(mk_explicit_key_map_trans(id_of_key_map=id_of_key_map))(StoreYourWrapping)
