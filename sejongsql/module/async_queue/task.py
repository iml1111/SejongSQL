from functools import wraps
from module.async_queue.base import SingletonInstane
from typing import Callable
from types import FunctionType


class TaskPool(SingletonInstane):

    def __init__(self):
        self.__pool = {}

    def __setitem__(self, name: str, func: Callable):
        if name in self.__pool:
            raise RuntimeError(
                f'이미 해당 이름의 태스크가 존재합니다: {name}')
        self.__pool[name] = func

    def __getattr__(self, name: str):
        return self.__pool.get(name)

    def __getitem__(self, name: str):
        return self.__pool.get(name)


def register_task(f):
    if not isinstance(f, FunctionType):
        raise RuntimeError(f'{f} is not FunctionType.')
    pool = TaskPool.instance()
    pool[f.__name__] = f
    return f

class Task:

    def __init__(self, name: str):
        pool = TaskPool.instance()
        if pool[name] is None:
            raise RuntimeError(f'해당 이름의 태스크는 등록되지 않았습니다: {name}')
        self.func = pool[name]

    def __call__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        return self


if __name__ == '__main__':

    @register_task
    def hello():
        print("hello world!")

    @register_task
    def add(a, b):
        print(a + b)

    t = Task('hello')(1,2,3)