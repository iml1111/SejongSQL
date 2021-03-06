"""
SQL Query 검증 모듈
"""
import json
from collections import namedtuple
import MySQLdb as mysql
from MySQLdb.connections import Connection
from MySQLdb._exceptions import OperationalError, ProgrammingError
from module.query_analyzer.uri import URI
from module.query_analyzer.mysql.select_query_firewall import is_safe_select_query


ValidationReport = namedtuple(
    'ValidationReport',
    ['result', 'msg', 'body', 'report_type'],
    defaults=(None, None, None, 'validation_report')
)


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
            if uri.dbname is None:
                self.mysql = mysql.connect(
                    host=uri.hostname,
                    port=uri.port,
                    user=uri.username,
                    passwd=uri.password,
                    charset='utf8',
                    cursorclass=mysql.cursors.DictCursor
                )
            else:
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

    def check_query(self, query: str, collect_explain: bool = False):
        """해당 쿼리가 올바른 SELECT 쿼리인지 판별"""
        if not isinstance(query, str):
            raise TypeError('query must be "str".')
        query = self.refine_query(query)

        safe, reason = is_safe_select_query(query)
        if not safe:
            return ValidationReport(result=False, msg='unsafe_query', body=reason)

        try:
            with self.mysql.cursor() as cursor:
                cursor.execute(f"EXPLAIN {query}")
                explain_table = cursor.fetchall()
                if collect_explain:
                    cursor.execute(f"EXPLAIN format=json {query}")
                    explain_json = cursor.fetchall()[0]['EXPLAIN']
        # 2) 실행오류 발생시 탈락
        except (OperationalError, ProgrammingError) as e:
            return ValidationReport(result=False, msg=f'execution_error: {e}')

        # 3) Explain select-type에 SELECT외에 하나라도 존재할 경우 탈락
        select_types = {i.get('select_type') for i in explain_table}
        if select_types & self.not_select:
            return ValidationReport(result=False, msg='not_select_query')

        return ValidationReport(
            result=True,
            msg='success',
            body={
                'explain': {
                    'table': explain_table,
                    'json': json.loads(explain_json)
                } if collect_explain else None
            }
        )

    @staticmethod
    def refine_query(query: str):
        return query.lower().strip()


if __name__ == '__main__':
    pass