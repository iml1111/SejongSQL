"""멀티프로세싱 관리 큐"""
from typing import Callable
from functools import wraps
from collections import deque
from multiprocessing import (
    Queue, Process, Manager, current_process
)
from module.async_queue.base import SingletonInstane
from module.async_queue.task import Task


class AsyncQueue(SingletonInstane):

    def __init__(self, worker_num: int = 3):
        self._sem_queue = Queue(maxsize=100)
        self._workers = []
        self._set_worker(worker_num=worker_num)

    def add(self, frozen_task: Task):
        if not isinstance(frozen_task, Task):
            raise RuntimeError(f'{frozen_task} is not Task.')
        self._sem_queue.put(frozen_task)

    def _set_worker(self, worker_num: int):
        workers = [
            Process(
                target=self._work,
                args=(i, self._sem_queue)
            )
            for i in range(worker_num)
        ]
        for worker in workers:
            worker.start()
        self._workers = workers

    @staticmethod
    def _work(worker_id: int, queue: Queue):
        p = current_process()
        print(f"[{p.pid}] Worker-{worker_id} Started...")
        while True:
            task = queue.get()
            task.execute()


def get_async_queue(*args, **kwargs):
    return AsyncQueue.instance(*args, **kwargs)

