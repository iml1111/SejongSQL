"""
SQL Query Explainer
"""
from collections import namedtuple
from module.query_analyzer.mysql.query_validator import SELECTQueryValidator
from module.query_analyzer.mysql.warning_report import *


ExplainReport = namedtuple(
    'ExplainReport',
    [
        'report_type',
        'expected_rows',
        'query_cost',
        'warnings',
        'metadata',
     ],
)


class QueryExplainer(SELECTQueryValidator):

    def explain_query(self, query: str):
        valid_report = self.check_query(query=query, collect_explain=True)
        if not valid_report.result:
            return valid_report
        norm_query = self._query_normalize(query)
        explain = valid_report.body['explain']
        warning_list = []
        try:
            query_cost = float(
                explain['json']['query_block']
                ['cost_info']['query_cost'])
        except KeyError:
            query_cost = 0

        # 지정된 Warning 검증 작업
        if self._full_table_scan(explain):
            warning_list.append(FULL_TABLE_SCAN)
        if self._no_join(explain, norm_query):
            warning_list.append(NO_JOIN)
        if self._file_sort(explain):
            warning_list.append(FILE_SORT)
        if self._impossible_condition(explain):
            warning_list.append(IMPOSSIBLE_CONDITION)
        if self._uncacheable(explain):
            warning_list.append(UNCACHEABLE)

        return ExplainReport(
            report_type='explain_report',
            expected_rows=sum([i['rows'] or 0 for i in explain['table']]),
            query_cost=query_cost,
            warnings=warning_list,
            metadata={
                'explain_record': explain['table'],
                'explain_json': explain['json'],
                'normalized_query': norm_query,
            }
        )

    def _full_table_scan(self, explain: dict):
        """
        # 해당 쿼리는 풀테이블 스캔 혹은 인덱스 풀스캔을 수행하고 있음
        - Type 중 all 혹은 index이면서 extra에 using where가 있는가?
        """
        records = explain['table']
        full_scan_types = ('all', 'index')
        for record in records:
            full_scan_type = (record['type'] or "none").lower() in full_scan_types
            extra = (record['Extra'] or "").lower()
            if full_scan_type and 'using where' in extra:
                return True
        return False

    def _no_join(self, explain: dict, query: str):
        """
        FIXME: 빈약한 검증 방식입니다...
        # 해당 쿼리는 Join이 사용되지 않았음.
        - query string join 문자열이 감지되지 않고,
        - 모든 파티션 테이블의 type에 eq_ref, ref가 존재하지 않으며,
        - 모든 파티션 테이블의 ref가 null인가?
        """
        types = set(self._get_elements(explain, 'type'))
        refs = set(self._get_elements(explain, 'ref'))

        join_not_in_query = 'join' not in query
        no_type_ref = not ({'eq_ref', 'ref'} & types)
        ref_null_or_const = (
            (not refs)
            or (len(refs) == 1 and 'const' in refs)
        )
        return (
            join_not_in_query
            and no_type_ref
            and ref_null_or_const
        )

    def _file_sort(self, explain: dict):
        """
        # 해당 쿼리는 filesort가 사용되었다.
        - extra 내부에서 filesort 문자열이 하나라도 있는가?
        """
        extras = self._get_elements(explain, 'Extra')
        return any(['filesort' in i for i in extras])

    def _impossible_condition(self, explain: dict):
        """
        # 테이블 구조상 해당 Where/having 구문은 반드시 False인 경우
        - extra 내부에 impossible where가 하나라도 있는가?
        """
        extras = self._get_elements(explain, 'Extra')
        return any(['impossible' in i for i in extras])

    def _uncacheable(self, explain: dict):
        """
        # 외부에 공급되는 모든 값에 대하여,
        캐싱이 불가능해 해당 UNION/서브쿼리를 매번 재실행
        """
        types = self._get_elements(explain, 'select_type')
        return any(['uncacheable' in i for i in types])

    @staticmethod
    def _get_elements(explain: dict, type: str):
        result = [i[type] for i in explain['table']]
        result = list(filter(lambda x: x, result))
        result = list(map(lambda x: x.lower(), result))
        return result

    @staticmethod
    def _query_normalize(query: str):
        return query.lower().strip().replace('\n', ' ')


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    from pprint import pprint

    load_dotenv(verbose=True)
    uri = os.getenv('SSQL_DB_URI')

    a = QueryExplainer(uri=uri)
    res = a.explain_query(
        """
        select * from sejongsql_11013c1a_853b_4b37_9160_a52ec81129e1.buytbl b 
        where num = price = 30
        """
    )
    pprint(res._asdict())