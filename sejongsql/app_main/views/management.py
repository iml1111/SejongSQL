import time
from rest_framework.views import APIView
from django.http import HttpResponse
from django.conf import settings
from module.response import OK
from module.async_queue import get_async_queue


class WorkerStatusView(APIView):
    def get(self, request, **path):
        q = get_async_queue(
            worker_num=settings.ASYNC_QUEUE_WORKER,
            qsize=settings.ASYNC_QUEUE_SIZE,
        )
        return OK({
            'workers': [str(i) for i in q.workers],
            'q_status': q.q_status,
        })