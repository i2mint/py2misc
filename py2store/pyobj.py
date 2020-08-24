from py2store.sources import Attrs

ddir = lambda o: [x for x in dir(o) if not x.startswith('_')]
