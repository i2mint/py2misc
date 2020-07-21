from py2json.w_glom import *

from warnings import warn

warn("This module was renamed and has a new home in py2json proper "
     "(not py2misc/py2json where you are now. "
     "Try import py2json.w_glom instead of py2misc.py2json.using_glom.",
     DeprecationWarning, stacklevel=2)
