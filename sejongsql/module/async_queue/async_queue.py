"""멀티프로세싱 관리 큐"""
import logging
from traceback import format_exc
from multiprocessing import (
    Queue, Process, current_process
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

    def add(self, frozen_task: Task):
        if not isinstance(frozen_task, Task):
            raise RuntimeError(
                f'{frozen_task} is not Task.')
        self.health_check()
        self._sem_queue.put(frozen_task)
        self.health_check()

    @property
    def workers(self):
        return self._workers

    @property
    def q_status(self):
        if self._sem_queue.full():
            return 'full'
        elif self._sem_queue.empty():
            return 'empty'
        else:
            return 'exists'

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
                logging.warning(
                    f'[WORKER] {worker.name} is Dead, '
                    f'Recovery start...'
                )
                worker.close()
                self._workers[idx] = Process(
                    target=self._work,
                    args=(self._sem_queue,)
                )
                self._workers[idx].start()

    @staticmethod
    def _work(queue: Queue):
        django.setup()
        p = current_process()
        worker_prefix = f"[WORKER] ({p.name})"
        logging.info(f"{worker_prefix} Started...")
        while True:
            task = queue.get()
            django.db.connections.close_all()
            logging.info(f"{worker_prefix} get task...")
            try:
                task.execute()
            except Exception as e:
                error_msg = format_exc()
                logging.error(f"{worker_prefix} {error_msg}")
                logging.info(f"{worker_prefix} aborted task...")
            else:
                logging.info(f"{worker_prefix} complete task...")


def get_async_queue(*args, **kwargs):
    return AsyncQueue.instance(*args, **kwargs)

