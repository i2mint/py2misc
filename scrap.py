# def foo(a: int = 0, b: int = 0, c=0):
#     """This is foo. It computes something"""
#     return (a * b) + c
#
#
# def bar(x, greeting='hello'):
#     """bar greets it's input"""
#     return f"{greeting} {x}"
#
#
# def confuser(a: int = 0, x: float = 3.14):
#     return (a ** 2) * x
#
#
# from py2misc import dispatch_funcs
#
# dispatch_funcs([foo, bar, confuser], 'dash')


def func(obj):
    return obj.a + obj.b


def other_func(obj):  # not used on target class instance
    return int(obj)


class A:
    e = 2

    def __init__(self, a=0, b=0, c=1, d=10):
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def target_method(self, x=3):
        t = func(self)
        tt = self.other_method(t)
        w = other_func(x.d)
        return x * tt / (self.e + w)

    def other_method(self, x=1):
        w = other_func(x)
        return self.c * x * w
