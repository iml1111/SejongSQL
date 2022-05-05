"""멀티프로세싱 관리 큐"""
import logging
from typing import Callable
from functools import wraps
from collections import deque
from multiprocessing import (
    Queue, Process, Manager, current_process
)
import django
from module.async_queue.base import SingletonInstane
from module.async_queue.task import Task


class AsyncQueue(SingletonInstane):

    def __init__(
        self,
        worker_num: int = 3,
        qsize: int = 100
    ):
        self._sem_queue = Queue(maxsize=qsize)
        self._workers = []
        self.set_workers(worker_num=worker_num)
        self._logger = logging.getLogger(__name__)

    def add(self, frozen_task: Task):
        if not isinstance(frozen_task, Task):
            raise RuntimeError(
                f'{frozen_task} is not Task.')
        self.health_check()
        self._sem_queue.put(frozen_task)

    @property
    def workers(self):
        return self._workers

    def set_workers(self, worker_num: int):
        workers = [
            Process(
                target=self._work,
                args=(self._sem_queue,)
            )
            for _ in range(worker_num)
        ]
        for worker in workers:
            worker.start()
        self._workers = workers

    def health_check(self):
        for idx, worker in enumerate(self._workers):
            if not worker.is_alive():
                self._logger.warning(
                    f'{worker.name} is Dead, '
                    f'Recovery start...'
                )
                worker.close()
                self._workers[idx] = Process(
                    target=self._work,
                    args=(self._sem_queue,)
                )

    @staticmethod
    def _work(queue: Queue):
        django.setup()
        p = current_process()
        worker_name = f"[{p.name}] Worker"
        print(f"{worker_name} Started...")
        while True:
            task = queue.get()
            print(f"{worker_name} get task...")
            task.execute()
            print(f"{worker_name} complete task...")


def get_async_queue(*args, **kwargs):
    return AsyncQueue.instance(*args, **kwargs)

