class ModuleNotFoundErrorNiceMessage:
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is ModuleNotFoundError:
            raise ModuleNotFoundError(f"""
It seems you don't have requred `{exc_val.name}` package.
Try installing it by running:

    pip install {exc_val.name}

in your terminal.
For more information: https://pypi.org/project/{exc_val.name}
            """)


class I2mintModuleNotFoundErrorNiceMessage:
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is ModuleNotFoundError:
            raise ModuleNotFoundError(f"""
It seems you don't have requred `{exc_val.name}` package. Not sure if this is the problem, but you could try:
    git clone https://github.com/i2mint/{exc_val.name}
in a place that your python path (i.e. PYTHONPATH environment variable).  
            """)


class SubscriptableType:
    """
    To make type ints that are subscriptable.
    If you're custom type is a container of sorts, you might want to say something about the type of it's contents.
    This is a way. Using the dunder: __class_getitem__

    >>> class A(SubscriptableType): ...
    >>> def f(a: A[str], b: A[int, float], c: int): ...
    >>> f.__annotations__
    {'a': 'util.A[str]', 'b': 'util.A[int, float]', 'c': <class 'int'>}
    """

    def __class_getitem__(cls, item):
        if not isinstance(item, tuple):
            return f"{cls.__module__}.{cls.__qualname__}[{item.__name__}]"
        else:
            return f"{cls.__module__}.{cls.__qualname__}[{', '.join([x.__name__ for x in item])}]"
