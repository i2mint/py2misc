from inspect import signature, Parameter, Signature


# Note: ParamsDict and Params have be replaced by i2.signature.Sig class

# TODO: Not really using this or Params competitor -- consider extending or deprecating
class ParamsDict(dict):
    """

    >>> def foo(a, b: int, c=None, d: str='hi') -> int: ...
    >>> def bar(b: float, d='hi'): ...
    >>> ParamsDict(foo)
    {'a': <Parameter "a">, 'b': <Parameter "b: int">, 'c': <Parameter "c=None">, 'd': <Parameter "d: str = 'hi'">}
    >>> p = ParamsDict(bar)
    >>> ParamsDict(p['b'])
    {'b': <Parameter "b: float">}
    >>> ParamsDict()
    {}
    >>> ParamsDict([p['d'], p['b']])
    {'d': <Parameter "d='hi'">, 'b': <Parameter "b: float">}
    """

    def __init__(self, obj=None):
        if obj is None:
            params_dict = dict()

        elif callable(obj):
            params_dict = dict(signature(obj).parameters)
        elif isinstance(obj, Parameter):
            params_dict = {obj.name: obj}
        else:
            try:
                params_dict = dict(obj)
            except TypeError:
                params_dict = {x.name: x for x in obj}

        super().__init__(params_dict)

    @classmethod
    def from_signature(cls, sig):
        """

        :param sig:
        :return:

        >>> from inspect import signature, Signature
        >>> def foo(a, b: int, c=None, d: str='hi') -> int: ...
        >>> sig = signature(foo)
        >>> assert isinstance(sig, Signature)
        >>> params = ParamsDict.from_signature(sig)
        >>> params
        {'a': <Parameter "a">, 'b': <Parameter "b: int">, 'c': <Parameter "c=None">, 'd': <Parameter "d: str = 'hi'">}
        """
        return cls(sig.parameters.values())

    @classmethod
    def from_callable(cls, obj):
        return cls.from_signature(signature(obj))

    def __add__(self, params):
        if isinstance(params, Parameter):
            self.__class__([params])
        elif isinstance(params, Signature):
            self.__class__.from_signature(params)
        else:
            pass

    def __setitem__(self, k, v):
        pass

    def validate(self):
        for k, v in self.items():
            assert isinstance(k, str), f"isinstance({k}, str)"
            assert isinstance(v, Parameter), f"isinstance({v}, Parameter)"
        return True


from i2.signatures import ensure_params


# TODO: Not really using this or ParamsDict competitor -- consider extending or deprecating
class Params(tuple):
    """

    >>> def foo(a, b: int, c=None, d: str='hi') -> int: ...
    >>> def bar(b: int, e=0): ...
    >>> Params.from_obj(foo) + Params.from_obj(bar)
    (<Parameter "a">, <Parameter "b: int">, <Parameter "c=None">, <Parameter "d: str = 'hi'">, <Parameter "e=0">)
    """

    @classmethod
    def from_obj(cls, obj=None):
        if obj is None:
            return cls()
        elif isinstance(obj, Params):
            return cls(x for x in obj)
        else:
            return cls(ensure_params(obj))

    # TODO: Will only work in nice situations -- extend to work in more situations
    def __add__(self, params):
        existing_params = set(self)
        existing_names = {p.name for p in existing_params}
        new_params = [p for p in Params(params) if p not in existing_params]
        if existing_names.intersection(p.name for p in new_params):
            raise ValueError(
                "You can't add two Params instances if they use the same names but "
                "different kind, annotation, or default. This was obtained when you tried to add"
                f"{self} and {params}")

        return Params(list(self) + [p for p in Params(params) if p not in existing_params])
