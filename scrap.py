


import os
from collections.abc import MutableMapping


class Persister(MutableMapping):
    def __len__(self):
        sum(1 for _ in self.__iter__())

    def clear(self):
        raise NotImplementedError("No way I'm allowing that!")


class SimpleFilePersister(Persister):
    def __init__(self, rootdir, mode='t'):
        assert mode in {'t', 'b', ''}, f"mode ({mode}) not valid"
        self.mode = mode
        self.rootdir = rootdir

    def __iter__(self):
        yield from os.listdir(self.rootdir)

    def __getitem__(self, k):
        with open(k, 'r' + self.mode) as fp:
            data = fp.read()
        return data

    def __setitem__(self, k, v):
        with open(k, 'w' + self.mode) as fp:
            fp.write(v)

    def __delitem__(self, k):
        os.remove(k)

    def __contains__(self, k):
        return os.path.isfile(k)




