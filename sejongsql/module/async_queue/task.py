from typing import Callable
from types import FunctionType


class frozen:

    def __init__(self, func: Callable):
        if not isinstance(func, FunctionType):
            raise RuntimeError(f'{func} is not FunctionType.')
        self.func = func

    def __call__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        return self

    def execute(self):
        return self.func(*self.args, *self.kwargs)


if __name__ == '__main__':

    def function(a, b):
        print(a + b)

    t = frozen(function)(1, 2)
    t.execute()
    t.execute()
