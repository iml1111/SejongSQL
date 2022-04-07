"""
SQL Query 검증 모듈
"""
from collections import namedtuple
import MySQLdb as mysql
from MySQLdb.connections import Connection
from MySQLdb._exceptions import OperationalError, ProgrammingError
from module.query_analyzer.uri import URI


Report = namedtuple('Report', ['result', 'msg'])


class SELECTQueryValidator:

    def __init__(
        self,
        uri: str = None,
        cursor: Connection = None
    ):
        """초기화시, 올바른 mysql uri 혹은 mysql Connection 객체 삽입"""
        if isinstance(cursor, Connection):
            self.mysql = cursor
        elif isinstance(uri, str):
            uri = URI(uri)
            if not uri.is_valid:
                raise RuntimeError('"uri" is incorrect scheme.')
            self.mysql = mysql.connect(
                host=uri.hostname,
                port=uri.port,
                user=uri.username,
                passwd=uri.password,
                db=uri.dbname,
                charset='utf8',
                cursorclass=mysql.cursors.DictCursor
            )
        else:
            raise RuntimeError('"uri" or "cursor" must required.')
        self.not_select = {'DELETE', 'UPDATE', 'INSERT', 'REPLACE'}

    def check_query(self, query: str):
        """해당 쿼리가 올바른 SELECT 쿼리인지 판별"""
        if not isinstance(query, str):
            raise TypeError('query must be "str".')
        query = self.refine_query(query)

        # 1) SELECT로 시작하지 않을 경우 탈락
        if not query.startswith('select'):
            return Report(result=False, msg='not_startswith_select')

        try:
            with self.mysql.cursor() as cursor:
                cursor.execute(f"EXPLAIN {query}")
                result = cursor.fetchall()
        # 2) 실행오류 발생시 탈락
        except (OperationalError, ProgrammingError) as e:
            return Report(result=False, msg=f'execution_error: {e}')

        # 3) Explain select-type에 SELECT외에 하나라도 존재할 경우 탈락
        select_types = {i.get('select_type') for i in result}
        if select_types & self.not_select:
            return Report(result=False, msg='not_select_query')

        return Report(result=True, msg='success')

    @staticmethod
    def refine_query(query: str):
        return query.lower().strip()


if __name__ == '__main__':
    uri = "mysql://root:hkw10256@localhost:3306/world"
    validator = SELECTQueryValidator(uri=uri)
    # 이미 connection 객체가 있을 경우,
    # SELECTQueryValidator(cursor=args) 인자로 직접 전달 가능.

    # 성공 예시
    correct_query = "select * from city;"
    report = validator.check_query(query=correct_query)
    print(report)

    # 1) 실패 예시
    incorrect1_query = "delete from city;"
    report = validator.check_query(query=incorrect1_query )
    print(report)

    # 2) 실패 예시
    incorrect2_query = "select * from 없는테이블;"
    report = validator.check_query(query=incorrect2_query)
    print(report)

    # 3) 실패 예시
    # 재현 불가능 ㅋㅋ...