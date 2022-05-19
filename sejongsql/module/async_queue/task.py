from typing import Callable
from types import FunctionType


class Task:

    def __init__(self, func: Callable):
        if not isinstance(func, FunctionType):
            raise RuntimeError(f'{func} is not FunctionType.')
        self.func = func
        self.args = tuple()
        self.kwargs = dict()

    def __call__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        return self

    def execute(self):
        return self.func(*self.args, **self.kwargs)


def freeze(func: Callable):
    return Task(func)


if __name__ == '__main__':

    def func(a, b):
        print(a + b)

    t = freeze(func)(a=1, b=2)
    t.execute()
    t.execute()
