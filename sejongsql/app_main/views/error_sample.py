from django.conf import settings
from rest_framework.views import APIView
from module.async_queue import get_async_queue, freeze
from module.response import OK
import time

class ErrorSample(APIView):
    def get(self, request):
        raise KeyError("500 SERVER ERROR TEST")


class AsyncTestView(APIView):
    def get(self, request):
        
        q = get_async_queue(
            worker_num=getattr(settings, 'ASYNC_QUEUE_WORKER', None),
            qsize=getattr(settings, 'ASYNC_QUEUE_SIZE', None),
        )
        q.add(freeze(hello_world)())
        return OK()


def hello_world():
    time.sleep(5)
    print("Hello World!!!!!")