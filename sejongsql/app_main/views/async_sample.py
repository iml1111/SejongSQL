import time
from rest_framework.views import APIView
from module.response import OK


from module.async_queue import get_async_queue, freeze
import MySQLdb
from app_main.models import User

# Sample Functions
def wait_and_hello(sec: int):
    """sec초간 기다렸다가 hello를 출력하는 함수"""
    time.sleep(sec)
    print(f"{sec}초 기다렸다가 Hello!!!!!!!!!!!!!!!!")

def mysql_connect():
    """임시로 만든 로컬 DB이기 때문에 테스트할 경우,
    적절히 인자 바꿔서 할 것."""
    conn = MySQLdb.connect(
        host='localhost',
        user='root',
        password='hkw10256',
        db='my1st_db',
    )
    cursor = conn.cursor()
    cursor.execute("select * from kospi_adjusted1")
    print("Result is", cursor.fetchone())
    cursor.close()
    conn.close()

def orm_connect():
    user = User.objects.filter(id='asd').first()
    print("ORM is", user)


class AsyncSample(APIView):

    def get(self, request, **path):
        """
        - worker_num (default=3)
            비동기 작업을 수행하기 위해 배치된 워커 프로세스 수.
            최대 N개의 처리만 동시적으로 수행하고
            나머지는 Queue에서 대기시키면서 순차적으로 불러옴.
        - qsize (default=100)
            비동기 대기 큐에 작업을 넣을 수 있는 최대 수
        - freeze
            함수를 그대로 실행시켜버리면 안되기 때문에
            함수의 이름, 필요 인자들을 그대로 동결시킨 채로
            실행시키기지 않고 보존시킴.

        * 주의사항
        - return 값에 의존하지 않는 함수여야 함. return 값을 걍 버림.
        """
        # 전역에 선언된 Async Task Queue 호출
        q = get_async_queue(worker_num=3, qsize=100)
        # 비동기 큐에 원하는 태스크 삽입.
        q.add(freeze(wait_and_hello)(sec=4))
        q.add(freeze(mysql_connect))
        q.add(freeze(orm_connect))

        return OK('Async Started, Check the log.')