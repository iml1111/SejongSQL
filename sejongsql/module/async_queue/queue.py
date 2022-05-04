"""멀티프로세싱 관리 큐"""
from multiprocessing import Queue
from module.async_queue.base import SingletonInstane


class AsyncQueue(SingletonInstane):

    def __init__(self):
        self.__queue = Queue()
