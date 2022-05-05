import time, random
from module.async_queue.task import freeze
from module.async_queue.async_queue import get_async_queue


def sleep(sec):
    print(f"{sec}초 쉴게요!")
    time.sleep(sec)
    print(f"다 쉬었어요!")

def add(a, b):
    print(f"{a} + {b} => {a + b}")


if __name__ == '__main__':
    q = get_async_queue()
    q.add(freeze(sleep)(3))
    q.add(freeze(add)(3, 2))