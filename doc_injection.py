from inspect import signature


def add_doc(func):
    t = ', '.join(signature(func).parameters)
    func.__doc__ = func.__doc__.format(t)
    return func


def foo(a, b):
    """Hi, I'm the doc
    {}
    bloo bloo"""


add_doc(foo)

print(help(foo))
