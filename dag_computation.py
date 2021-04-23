from inspect import signature, Signature


# Note: A better version of this lives now on lined, an otosense repo and pip installable package
class Compose:
    def __init__(self, *funcs):
        """Performs function composition.
        That is, get a callable that is equivalent to a chain of callables.
        For example, if `f`, `h`, and `g` are three functions, the function
        ```
            c = Compose(f, h, g)
        ```
        is such that, for any valid inputs `args, kwargs` of `f`,
        ```
        c(*args, **kwargs) == g(h(f(*args, **kwargs)))
        ```
        (assuming the functions are deterministic of course).

        >>> def first(a, b=1):
        ...     return a * b
        >>>
        >>> def last(c) -> float:
        ...     return c + 10
        >>>
        >>> f = Compose(first, last)
        >>>
        >>> assert f(2) == 12
        >>> assert f(2, 10) == 30
        >>>
        >>> from inspect import signature
        >>>
        >>> assert str(signature(f)) == '(a, b=1) -> float'
        >>> assert signature(f).parameters == signature(first).parameters
        >>> assert signature(f).return_annotation == signature(last).return_annotation == float
        >>>
        >>> # Border case: One function only
        >>> same_as_first = Compose(first)
        >>> assert same_as_first(42) == first(42)
        """
        self.funcs = funcs
        # Determining what the first and last function is.
        n_funcs = len(self.funcs)
        if n_funcs == 0:
            raise ValueError("You need to specify at least one function!")
        elif n_funcs == 1:
            first_func = last_func = funcs[0]
        else:
            first_func, *_, last_func = funcs
        # Finally, let's make the __call__ have a nice signature.
        # Argument information from first func and return annotation from last func
        self.__signature__ = Signature(signature(first_func).parameters.values(),
                                       return_annotation=signature(last_func).return_annotation)

    def __call__(self, *args, **kwargs):
        first_func, *other_funcs = self.funcs
        out = first_func(*args, **kwargs)
        for func in other_funcs:
            out = func(out)
        return out


from collections import defaultdict
from functools import cached_property


# Class to represent a graph
class Digraph:
    def __init__(self, nodes_adjacent_to=None):
        nodes_adjacent_to = nodes_adjacent_to or dict()
        self.nodes_adjacent_to = defaultdict(list, nodes_adjacent_to)  # adjacency list (look it up)
        # self.n_vertices = vertices  # No. of vertices

    # function to add an edge to graph
    def add_edge(self, u, v):
        self.nodes_adjacent_to[u].append(v)

        # A recursive function used by topologicalSort

    def _helper(self, v, visited, stack):

        # Mark the current node as visited.
        visited[v] = True

        # Recur for all the vertices adjacent to this vertex
        for i in self.nodes_adjacent_to[v]:
            if visited[i] == False:
                self._helper(i, visited, stack)

                # Push current vertex to stack which stores result
        stack.insert(0, v)

        # The function to do Topological Sort. It uses recursive

    # topologicalSortUtil()
    def topological_sort(self):
        # Mark all the vertices as not visited
        visited = [False] * self.n_vertices
        stack = []

        # Call the recursive helper function to store Topological
        # Sort starting from all vertices one by one
        for i in range(self.n_vertices):
            if visited[i] == False:
                self._helper(i, visited, stack)

                # Print contents of stack
        return stack
