from py2store import KvReader, cache_iter

ddir = lambda o: [x for x in dir(o) if not x.startswith('_')]


def not_underscore_prefixed(x):
    return not x.startswith('_')


@cache_iter(name='Ddir')
class Ddir(KvReader):
    def __init__(self, obj, key_filt=not_underscore_prefixed):
        self._source = obj
        self._key_filt = key_filt

    def __iter__(self):
        yield from filter(self._key_filt, dir(self._source))

    def __getitem__(self, k):
        return self.__class__(getattr(self._source, k))

    def __repr__(self):
        return f"{self.__class__.__qualname__}({self._source}, {self._key_filt})"
